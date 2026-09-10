"""Target <-> record-id mapping and the deterministic text matcher shared by the metrics.

`benchmark/target_map.json`  (produced in Phase 3 after freeze #1, reviewed by the coordinator)
    {case_id: [{"target_index": int, "record_ids": [id, ...]}, ...]}
DECISIONS #13 / #18(5): a target maps to a SET of ids and is present if ANY mapped id is on the
card. `propose_mapping` writes a PROPOSED map from token overlap; it never commits anything.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Iterable

import config
from eval.cases import CaseInput, Target

log = logging.getLogger("eval.mapping")

TARGET_MAP_PATH = Path(config.ROOT) / "benchmark" / "target_map.json"

# phrase -> canonical token, applied before tokenising (both sides, so it is symmetric)
_ALIASES = [
    (r"jugular venous (?:pressure|pulse|distension)", "jvp"), (r"third heart sound", "s3"), (r"fourth heart sound", "s4"),
    (r"point[- ]of[- ]care (?:ultrasound|ultrasonography)|bedside ultrasound", "pocus"), (r"electrocardiogram|ekg", "ecg"),
    (r"medication (?:review|reconciliation|history|list)|drug chart|\bmar\b", "medreview"), (r"postural", "orthostatic"),
    (r"head impulse,? nystagmus,? (?:and )?test of skew", "hints"), (r"capillary refill(?: time)?", "caprefill"),
    (r"costovertebral angle", "cva"), (r"digital rectal exam(?:ination)?", "dre"), (r"blood pressure", "bp"), (r"heart rate", "hr"),
    (r"respiratory rate", "rr"), (r"mental status", "mentalstatus"), (r"loss of consciousness", "loc"), (r"last[- ]known[- ]well", "lkw"),
    (r"rlq|right lower quadrant", "rlq"), (r"llq|left lower quadrant", "llq"), (r"ruq|right upper quadrant", "ruq"),
    (r"abdominojugular|hepatojugular", "ajr"), (r"passive leg raise", "plr"), (r"confusion assessment method", "cam"),
    (r"dix[- ]hallpike", "dixhallpike"), (r"witness(?:ed)? account|collateral history", "witness"), (r"tongue[- ]biting|bitten tongue", "tonguebite"),
    (r"post[- ]?(?:event|ictal) confusion", "postictal"), (r"breath sounds", "breathsounds"), (r"nuchal rigidity|neck stiffness", "neckstiff"),
    (r"pronator drift", "drift"), (r"calf (?:circumference|swelling|asymmetry)", "calf"), (r"orthostatic (?:vital signs|vitals|bp|hypotension)", "orthostatic"),
]
_ALIAS_RX = [(re.compile(p, re.I), tok) for p, tok in _ALIASES]
_STOP = frozenset("""a an the and or of for to in on at by with without vs versus from into over under than then as is are be been was were
any all both each per via if when whether while about after before during since until within ask asks asking check checks assess assessment
assessing examine examination exam examined look looking observe perform performed test tests testing evaluate evaluation evaluating measure
measured obtain obtaining document review screen screening bedside patient patients his her their its this that these those it he she they
item items sign signs finding findings presence absence new known should must may can could would do does not no yes also only e g ie eg
include including using use used ie i e etc versus level levels min minutes minute sec seconds second hour hours h s cm mm mmhg one two three
right left side sides bilateral bilaterally unilateral""".split())
_TOKEN_RX = re.compile(r"[a-z0-9]+")


def _stem(tok: str) -> str:
    for suf in ("ies", "ing", "ed", "es", "s"):
        if len(tok) > len(suf) + 3 and tok.endswith(suf):
            return tok[: -len(suf)] + ("y" if suf == "ies" else "")
    return tok


def tokens(text: str) -> set[str]:
    """Content tokens: aliases folded, lowercase, stop words out, light stemming."""
    t = (text or "").lower()
    for rx, tok in _ALIAS_RX:
        t = rx.sub(f" {tok} ", t)
    return {_stem(w) for w in _TOKEN_RX.findall(t) if w not in _STOP and len(w) > 1 and not w.isdigit()}


def components(text: str) -> list[str]:
    """A compound target's components: split on ';', ',', '/', ' and ', ' or ' and parentheses.
    Component-level matching is the text analogue of the ANY-id rule (DECISIONS #13)."""
    t = re.sub(r"[()]", ",", text or "")
    parts = re.split(r"\s*(?:;|,|/|\band\b|\bor\b|\bplus\b|\bwith\b)\s*", t)
    return [p.strip() for p in parts if p.strip()]


def overlap(a: set[str], b: set[str]) -> float:
    """Share of a's tokens found in b (0 if a is empty)."""
    return len(a & b) / len(a) if a else 0.0


def jaccard(a: Iterable[Any], b: Iterable[Any]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def phrase_matches(phrase: str, item_text: str, threshold: float = 0.5) -> bool:
    """A phrase (target, component, or record title) is 'in' an item if >= threshold of its
    content tokens appear in the item and at least two tokens overlap (one if the phrase has <= 2)."""
    p, i = tokens(phrase), tokens(item_text)
    if not p:
        return False
    hit = len(p & i)
    need = 1 if len(p) <= 2 else 2
    return hit >= need and overlap(p, i) >= threshold


def target_text_matches(target_text: str, item_text: str) -> bool:
    """Whole target or any component (>= 2 content tokens, or a whole short target) matches."""
    if phrase_matches(target_text, item_text):
        return True
    comps = components(target_text)
    if len(comps) <= 1:
        return False
    item_toks = tokens(item_text)
    for comp in comps:
        ct = tokens(comp)
        if len(ct) >= 2:
            if phrase_matches(comp, item_text, threshold=0.6):
                return True
        elif len(ct) == 1:
            tok = next(iter(ct))
            if len(tok) >= 4 and tok in item_toks:  # e.g. "rebound", "rigidity"; short/generic tokens never match alone
                return True
    return False


# --- mapping file --------------------------------------------------------------------
def load_target_map(path: str | Path | None = None) -> dict[str, dict[int, list[str]]]:
    """{case_id: {target_index: [record_ids]}}; {} when the file does not exist."""
    p = Path(path or TARGET_MAP_PATH)
    if not p.exists():
        log.warning("target map %s not found: targets are unmapped (recall falls back to text matching)", p)
        return {}
    data = json.loads(p.read_text())
    out: dict[str, dict[int, list[str]]] = {}
    for case_id, entries in data.items():
        if case_id.startswith("_"):
            continue
        out[case_id] = {int(e["target_index"]): list(e.get("record_ids") or []) for e in entries}
    return out


def attach(cases: list[CaseInput], target_map: dict[str, dict[int, list[str]]]) -> None:
    """Fill Target.mapped_ids in place (a variant inherits its base case's mapping)."""
    for c in cases:
        m = target_map.get(c.case_id) or target_map.get(c.base_case_id) or {}
        for t in c.targets:
            t.mapped_ids = list(m.get(t.index, []))


def library_coverage(cases: list[CaseInput], verified_ids: set[str]) -> dict[str, Any]:
    """Targets with >= 1 mapped id that exists in the verified store / all targets (per base case, once)."""
    seen: set[str] = set()
    total = covered = mapped_any = 0
    unmapped: list[dict[str, Any]] = []
    for c in cases:
        if c.base_case_id in seen:
            continue
        seen.add(c.base_case_id)
        for t in c.targets:
            total += 1
            if t.mapped_ids:
                mapped_any += 1
            if any(i in verified_ids for i in t.mapped_ids):
                covered += 1
            else:
                unmapped.append({"case_id": c.base_case_id, "target_index": t.index, "item": t.item, "mapped_ids": t.mapped_ids})
    return {
        "targets": total, "mapped_to_any_id": mapped_any, "mapped_to_verified": covered,
        "coverage": covered / total if total else None, "uncovered": unmapped,
    }


# --- proposal helper ---------------------------------------------------------------------
def _id_tokens(entry: dict[str, Any]) -> set[str]:
    return tokens(entry.get("title", "")) | tokens(entry["id"].replace("_", " "))


def propose_mapping(
    cases: list[CaseInput], ids_path: str | Path | None = None, out_path: str | Path | None = None,
    restrict_to: set[str] | None = None, min_score: float = 0.34, max_ids: int = 3, entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deterministic token-overlap proposal target -> ids. Writes a PROPOSED file for the
    coordinator to review; never touches git and never writes benchmark/target_map.json itself.
    `entries` ([{id, title}]) overrides the ids file (used to score against a store's own titles)."""
    ids = entries if entries is not None else json.loads(Path(ids_path or config.IDS_PATH).read_text())["ids"]
    if restrict_to is not None:
        ids = [e for e in ids if e["id"] in restrict_to]
    id_toks = {e["id"]: _id_tokens(e) for e in ids}
    proposal: dict[str, Any] = {
        "_status": "PROPOSED by eval.mapping.propose_mapping (token overlap). Coordinator must review, "
                   "rename to benchmark/target_map.json, and commit as freeze #2. Not authoritative.",
        "_rule": f"score = mean(overlap(target->id), overlap(id->target)) over content tokens; keep ids with score >= {min_score}, max {max_ids}; "
                 "compound targets also scored per component (DECISIONS #13).",
    }
    seen: set[str] = set()
    for c in cases:
        if c.base_case_id in seen:
            continue
        seen.add(c.base_case_id)
        entries = []
        for t in c.targets:
            phrases = [t.item] + [p for p in components(t.item) if len(tokens(p)) >= 2]
            scored: dict[str, float] = {}
            for rid, it in id_toks.items():
                best = 0.0
                for ph in phrases:
                    pt = tokens(ph)
                    if not pt or not it:
                        continue
                    s = (overlap(pt, it) + overlap(it, pt)) / 2
                    if ph is t.item:
                        s = max(s, overlap(pt, it))  # long id titles: reward covering the target fully
                    best = max(best, s)
                if best >= min_score:
                    scored[rid] = round(best, 3)
            top = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))[:max_ids]
            entries.append({"target_index": t.index, "item": t.item, "record_ids": [r for r, _ in top], "scores": dict(top)})
        proposal[c.base_case_id] = entries
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(proposal, indent=1))
        log.info("PROPOSED target map written to %s (review before use)", out_path)
    return proposal
