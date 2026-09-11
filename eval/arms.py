"""The three comparator arms, each returning one normalised ArmOutput, persisted as JSON.

  A  Bedside Brief          bedside_brief.pipeline.brief (parse -> retrieve -> LLM rank -> render -> validate)
  B  Retrieval-only         parse (same LLM parser) -> retrieve_fixed_order -> render (no ranker) -> validate
  C  Generic LLM            the rubric's prompt verbatim, same model, raw text kept, parsed by eval.item_parser

Persistence: eval/runs/{timestamp}/{arm}/{case_id}.json + manifest.json. `run_case_arm` skips
any (arm, case) that already succeeded, so a timed-out run can be resumed; a stored failure is
retried rather than counted as a finished empty card.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config
from bedside_brief import pipeline
from bedside_brief import retrieve as retrieve_mod
from bedside_brief.parser import parse_oneliner
from bedside_brief.render import render_card
from bedside_brief.validate import validate_or_block
from eval.cases import CaseInput
from eval.item_parser import items_from_card, parse_free_text

log = logging.getLogger("eval.arms")

ARMS = ("A", "B", "C")
# evaluation_rubric.md, arm C — verbatim.
GENERIC_PROMPT = (
    "Given this presentation, what history, physical examination, and bedside tests should I perform? "
    "Include any diagnostic performance data you know."
)
C_SCHEMA: dict[str, Any] = {
    "title": "free_text_answer",
    "type": "object",
    "additionalProperties": False,
    "required": ["answer"],
    "properties": {"answer": {"type": "string"}},
}
# The shared LLM client only speaks JSON; this wrapper is the smallest constraint that keeps
# the answer itself free text. It adds no content guidance.
C_SYSTEM = 'Reply with a JSON object with one key, "answer", whose value is your complete free-text answer (plain text or markdown).'
# Arm C has no parser contract; an "ask first" is inferred when the text declines to rank without more information.
_C_ASK_FIRST = re.compile(
    r"(?:i(?:'d| would) need (?:more|to know|additional)|(?:more|additional|further) (?:information|details?|history|context) (?:is|are|would be) (?:needed|required|necessary|essential)"
    r"|(?:insufficient|not enough|too little|limited) (?:information|detail|history|context)|before (?:i|we|one) can (?:rank|prioriti[sz]e|narrow|tailor|give a focused))",
    re.I,
)


@dataclass
class ArmOutput:
    arm: str
    case_id: str
    base_case_id: str
    variant: str
    model: str
    items: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    ask_first: bool = False
    blocked_items: list[str] = field(default_factory=list)
    error: str | None = None
    created_at: str = ""

    @property
    def record_ids(self) -> list[str]:
        return [i["record_id"] for i in self.items if i.get("record_id")]

    @property
    def texts(self) -> list[str]:
        return [i["text"] for i in self.items]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ArmOutput":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})  # type: ignore[arg-type]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _base(arm: str, case: CaseInput, llm: Any) -> ArmOutput:
    return ArmOutput(arm=arm, case_id=case.case_id, base_case_id=case.base_case_id, variant=case.variant,
                     model=str(getattr(llm, "model", "?")), created_at=_now())


def _card_output(out: ArmOutput, card: dict[str, Any], validation: dict[str, Any], mode: str) -> ArmOutput:
    out.items = [i.to_dict() for i in items_from_card(card, mode)]
    out.ask_first = bool(card.get("ask_first"))
    out.blocked_items = list((card.get("blocked") or {}).get("removed") or [])
    out.raw["card"] = card
    out.raw["validation"] = validation
    return out


def run_arm_a(case: CaseInput, llm: Any, db_path: str | Path | None = None, limits: Any = config, mode: str = "default") -> ArmOutput:
    """Arm A = the product: bedside_brief.pipeline.brief."""
    out = _base("A", case, llm)
    result = pipeline.brief(case.oneliner, llm, db_path, limits)
    out.raw = {"parsed": result["parsed"], "candidates": result["candidates"], "chosen": result["chosen"]}
    return _card_output(out, result["card"], result["validation"], mode)


def run_arm_b(case: CaseInput, llm: Any, db_path: str | Path | None = None, limits: Any = config, mode: str = "default") -> ArmOutput:
    """Arm B = same parser + store, retrieval order as-is, truncated to card limits, no ranker."""
    out = _base("B", case, llm)
    db_path = Path(db_path or config.DB_PATH)
    parsed = parse_oneliner(case.oneliner, llm)
    sections = retrieve_mod.retrieve_fixed_order(parsed, db_path, pocus_enabled=limits.POCUS_ENABLED, limits=limits)
    records_by_id = {c.id: c.record for cands in sections.values() for c in cands}
    chosen = retrieve_mod.to_chosen(sections)
    card = render_card(chosen, records_by_id, parsed, limits)
    card, res = validate_or_block(card, records_by_id)
    out.raw = {"parsed": parsed, "chosen": chosen}
    return _card_output(out, card, {"ok": res.ok, "violations": list(res.violations), "bad_item_ids": list(res.bad_item_ids)}, mode)


def run_arm_c(case: CaseInput, llm: Any, mode: str = "default") -> ArmOutput:
    """Arm C = generic unconstrained prompt, same model; raw text kept; deterministic item parse."""
    out = _base("C", case, llm)
    reply = llm.complete_json(C_SYSTEM, f"{GENERIC_PROMPT}\n\nPresentation: {case.oneliner}", C_SCHEMA)
    text = str(reply.get("answer") or "")
    out.raw = {"prompt": GENERIC_PROMPT, "text": text}
    out.items = [i.to_dict() for i in parse_free_text(text, mode)]
    out.ask_first = bool(_C_ASK_FIRST.search(text))
    return out


RUNNERS = {"A": run_arm_a, "B": run_arm_b, "C": run_arm_c}


def run_arm(arm: str, case: CaseInput, llm: Any, db_path: str | Path | None = None, limits: Any = config, mode: str = "default") -> ArmOutput:
    """Never raises: a failed arm is an ArmOutput with `error` set and no items (counted as a miss)."""
    try:
        if arm == "C":
            return run_arm_c(case, llm, mode)
        return RUNNERS[arm](case, llm, db_path, limits, mode)
    except Exception as exc:  # noqa: BLE001 - the run must continue across 108 inputs; the error is stored and reported
        log.error("arm %s case %s failed: %s: %s", arm, case.case_id, type(exc).__name__, exc)
        out = _base(arm, case, llm)
        out.error = f"{type(exc).__name__}: {exc}"
        out.raw = {"traceback": traceback.format_exc()[-2000:]}
        return out


# --- persistence -------------------------------------------------------------------------
def output_path(run_dir: str | Path, arm: str, case_id: str) -> Path:
    return Path(run_dir) / arm / f"{case_id}.json"


def save_output(run_dir: str | Path, out: ArmOutput) -> Path:
    p = output_path(run_dir, out.arm, out.case_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out.to_dict(), indent=1, sort_keys=True))
    return p


def load_output(path: str | Path) -> ArmOutput:
    return ArmOutput.from_dict(json.loads(Path(path).read_text()))


def run_case_arm(arm: str, case: CaseInput, llm: Any, run_dir: str | Path, db_path: str | Path | None = None,
                 limits: Any = config, mode: str = "default", force: bool = False) -> tuple[ArmOutput, bool]:
    """(output, ran): resumable — an existing SUCCESSFUL file is loaded, not recomputed, unless force.

    A stored failure is retried. `run_arm` never raises: a case that blew up is saved with `error`
    set and no items, so treating any existing file as done would let a transient failure — or one
    the code has since been fixed for — be counted as a real empty card in the reported metrics.
    """
    p = output_path(run_dir, arm, case.case_id)
    if p.exists() and not force:
        prior = load_output(p)
        if not prior.error:
            return prior, False
        log.info("arm %s case %s: retrying a stored failure (%s)", arm, case.case_id, prior.error)
    out = run_arm(arm, case, llm, db_path, limits, mode)
    save_output(run_dir, out)
    return out, True


def load_outputs(run_dir: str | Path, arms: tuple[str, ...] = ARMS) -> dict[str, dict[str, ArmOutput]]:
    """{arm: {case_id: ArmOutput}} for whatever exists in the run dir."""
    found: dict[str, dict[str, ArmOutput]] = {}
    for arm in arms:
        d = Path(run_dir) / arm
        if d.is_dir():
            found[arm] = {p.stem: load_output(p) for p in sorted(d.glob("*.json"))}
    return found


def git_head() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=config.ROOT, capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return None


def write_manifest(run_dir: str | Path, model: str, cases: list[CaseInput], args: dict[str, Any], extra: dict[str, Any] | None = None) -> Path:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / "manifest.json"
    manifest = json.loads(p.read_text()) if p.exists() else {"started_at": _now()}
    outputs = load_outputs(run_dir)
    manifest.update({
        "model": model,
        "git_head": git_head(),
        "frozen_commits": sorted({c.frozen_commit for c in cases}),
        "unfrozen_cases": sorted({c.base_case_id for c in cases if not c.frozen_commit}),
        "updated_at": _now(),
        "cases": {"inputs": len(cases), "base": sum(c.variant == "base" for c in cases),
                  "perturbation_pairs": sum(c.variant == "p1" for c in cases), "noise_variants": sum(c.variant == "n1" for c in cases)},
        "counts": {arm: {"outputs": len(o), "errors": sum(1 for x in o.values() if x.error)} for arm, o in outputs.items()},
        "args": args,
    })
    if extra:
        manifest.update(extra)
    p.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    return p
