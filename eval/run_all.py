"""CLI orchestrator: cases -> store -> arms A/B/C (resumable) -> metrics -> error analysis -> report -> judging queue.

  python3 -m eval.run_all --smoke                       # 3 files (9 inputs), FakeLLM, synthetic store, minutes, offline
  python3 -m eval.run_all --arms A,B,C                  # frozen benchmark, live model (config.py), eval/runs/<timestamp>/
  python3 -m eval.run_all --run-dir eval/runs/<ts>      # resume: existing (arm, case) files are skipped
  --cases <glob|dir>  --allow-unfrozen  --mode default|ecg_bedside|mar_offbedside (item classification stored on outputs)
"""
from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config
from bedside_brief import store
from bedside_brief.llm import FakeLLM
from eval import error_analysis, judging_export, mapping, report
from eval.arms import ARMS, load_outputs, run_case_arm, write_manifest
from eval.cases import CaseInput, load_cases
from eval.metrics import compute_metrics, write_metrics

log = logging.getLogger("eval.run_all")

SMOKE_C_TEXT = """Given this presentation, here is my approach:
History:
1. Ask about exertional onset and any prodrome (exertional syncope has sensitivity 85% for aortic stenosis; Etchells et al., 1997).
2. Ask about palpitations before the event and family history of sudden death.
Physical examination:
- Auscultate for a late-peaking systolic murmur with a soft S2 (LR+ 12.7 in one series).
- Orthostatic vital signs at 1 and 3 minutes.
- Carotid sinus massage.
Tests:
- 12-lead ECG
- Echocardiogram
- Troponin and BMP
"""


class SmokeState:
    """Mutable holder so the FakeLLM callable can see which case is being run."""

    case: CaseInput | None = None


def smoke_llm(state: SmokeState) -> FakeLLM:
    """Offline stand-in that answers the parser, ranker and arm-C prompts deterministically."""

    def reply(system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        title = schema.get("title")
        case = state.case
        if title == "oneliner_parse":
            dxs = [{"dx": "aortic_stenosis", "weight": 1.0}, {"dx": "orthostatic_hypotension", "weight": 0.6}, {"dx": "hypovolemic_hemorrhagic_shock", "weight": 0.4}]
            if case and case.variant == "p1":
                dxs = [{"dx": "orthostatic_hypotension", "weight": 1.0}, {"dx": "hypovolemic_hemorrhagic_shock", "weight": 0.7}]
            return {"chief_complaint": user[:60], "presentation": case.presentation if case else "syncope", "time_course": "acute",
                    "modifiers": [], "differentials": dxs, "indication_tags": ["exertional"],
                    "missing_features": ["exertional vs positional"] if case and case.underspecified_expected else []}
        if title == "card_choice":
            cands = json.loads(user)["candidates"]
            chosen: dict[str, list[dict[str, str]]] = {"ask": [], "examine": [], "pocus": []}
            for c in cands:
                sec = {"history": "ask", "exam": "examine", "functional": "examine", "pocus": "pocus"}[c["type"]]
                if len(chosen[sec]) < 2:
                    chosen[sec].append({"id": c["id"], "rationale": "Changes the next step."})
            return chosen
        if title == "free_text_answer":
            return {"answer": SMOKE_C_TEXT}
        raise ValueError(f"smoke LLM: unknown schema {title!r}")

    return FakeLLM(reply, model="fake-model-smoke")


def build_smoke_store(run_dir: Path) -> Path:
    """Synthetic verified store from tests/conftest.py (reused fixtures), indexed under the run dir."""
    from tests.conftest import VERIFIED, write_record  # reuse the fixtures' records

    verified_dir = run_dir / "smoke_store" / "verified"
    for rec in VERIFIED:
        write_record(verified_dir, copy.deepcopy(rec))
    db = run_dir / "smoke_index.sqlite"
    saved = config.RECORDS_VERIFIED
    config.RECORDS_VERIFIED = verified_dir
    try:
        store.build_index(db)
    finally:
        config.RECORDS_VERIFIED = saved
    return db


def extracted_ids() -> set[str]:
    return {p.name.split("__", 1)[0] for p in Path(config.RECORDS_EXTRACTED).glob("*__*.json")}


def run(args: argparse.Namespace) -> Path:
    smoke = args.smoke
    run_dir = Path(args.run_dir) if args.run_dir else Path(config.EVAL_RUNS) / (("smoke_" if smoke else "") + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    arms = tuple(a.strip().upper() for a in args.arms.split(",") if a.strip())
    for a in arms:
        if a not in ARMS:
            raise SystemExit(f"unknown arm {a!r}; choose from {ARMS}")

    pattern = args.cases or (str(Path(config.BENCHMARK_CASES) / "syncope_00*.json") if smoke else None)
    cases = load_cases(pattern, allow_unfrozen=args.allow_unfrozen or smoke, limit=3 if smoke else None)
    if smoke:
        log.warning("smoke mode: FakeLLM, synthetic store, unfrozen cases allowed; results are NOT evidence")

    # store
    if smoke:
        db_path = build_smoke_store(run_dir)
    else:
        db_path = Path(config.DB_PATH)
        store.build_index(db_path)
    records_by_id = store.load_index(db_path)
    verified_ids = {i for i, r in records_by_id.items() if r.get("tier") == "verified"}
    log.info("store: %d verified records indexed at %s", len(verified_ids), db_path)

    # mapping (freeze #2 artefact). A missing map is only worked around in smoke mode.
    target_map = mapping.load_target_map(args.target_map) if not smoke else {}
    if not target_map:
        proposed = run_dir / "target_map.proposed.json"
        entries = [{"id": i, "title": records_by_id[i]["identity"]["title"]} for i in sorted(verified_ids)] if smoke else None
        mapping.propose_mapping(cases, out_path=proposed, restrict_to=verified_ids or None, entries=entries)
        if smoke:
            target_map = mapping.load_target_map(proposed)
        else:
            log.warning("no benchmark/target_map.json: recall relies on text matching; a PROPOSED map was written to %s for review", proposed)
    mapping.attach(cases, target_map)

    # LLM
    state = SmokeState()
    if smoke:
        llm: Any = smoke_llm(state)
    else:
        from bedside_brief.llm import LLMClient

        llm = LLMClient()
        llm.startup_check()
    model = str(getattr(llm, "model", "?"))
    cli_args = {k: v for k, v in vars(args).items()}
    write_manifest(run_dir, model, cases, cli_args)

    # arms (resumable)
    ran = skipped = 0
    for arm in arms:
        for case in cases:
            state.case = case
            _, did_run = run_case_arm(arm, case, llm, run_dir, db_path, config, args.mode)
            ran += did_run
            skipped += not did_run
        write_manifest(run_dir, model, cases, cli_args)
    log.info("arms done: %d ran, %d resumed from disk", ran, skipped)

    # metrics -> error analysis -> report -> judging queue
    outputs = load_outputs(run_dir, arms)
    metrics = compute_metrics(cases, outputs, records_by_id, config, extracted_ids())
    write_metrics(metrics, run_dir)
    if "A" in outputs:
        error_analysis.write(metrics, run_dir, "A")
    report.write_report(run_dir)
    judging_export.export(run_dir, cases, all_cases=args.judge_all, arms=arms)
    write_manifest(run_dir, model, cases, cli_args, {"finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    return run_dir


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", default=None, help="output dir (default eval/runs/<timestamp>); pass an existing one to resume")
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--cases", default=None, help="glob or dir of benchmark files (default: benchmark/cases)")
    ap.add_argument("--smoke", action="store_true", help="3 case files, FakeLLM, synthetic store; offline")
    ap.add_argument("--allow-unfrozen", action="store_true", help="run even if a case has an empty frozen_commit")
    ap.add_argument("--mode", default="default", choices=("default", "ecg_bedside", "mar_offbedside"), help="classifier mode stored on item outputs (metrics always report all three)")
    ap.add_argument("--target-map", default=None, help="path to target_map.json (default benchmark/target_map.json)")
    ap.add_argument("--judge-all", action="store_true", help="judging queue for every case instead of 12 x 3 arms")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_dir = run(args)
    print(f"run dir: {run_dir}\n" + (run_dir / "metrics.md").read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
