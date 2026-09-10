"""Owner judging queue: shuffled, arm-blinded CSV of items + a separate sealed key file.

CSV columns: item_uid, case_id, presentation, input_oneliner, item_text, relevance, safety
(relevance / safety left blank for the owner: relevant|marginal|irrelevant, flag|no flag).
The arm lives ONLY in judging_key.json {item_uid: {arm, case_id, item_index, record_id}}.
Default queue: 12 base cases (the first base case of each presentation) x 3 arms; --all for everything.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from eval.arms import ARMS, load_outputs
from eval.cases import CaseInput, load_cases
from eval.item_parser import strip_formatting

CSV_COLUMNS = ["item_uid", "case_id", "presentation", "input_oneliner", "item_text", "relevance", "safety"]
RELEVANCE = ("relevant", "marginal", "irrelevant")
SAFETY = ("flag", "no flag")


def default_case_ids(cases: list[CaseInput], per_presentation: int = 1) -> list[str]:
    """First `per_presentation` base case(s) per presentation, sorted by presentation."""
    chosen: dict[str, list[str]] = {}
    for c in sorted((c for c in cases if c.variant == "base"), key=lambda c: c.case_id):
        lst = chosen.setdefault(c.presentation, [])
        if len(lst) < per_presentation:
            lst.append(c.case_id)
    return [cid for p in sorted(chosen) for cid in chosen[p]]


def _uid(run_dir: str, arm: str, case_id: str, index: int) -> str:
    return hashlib.sha1(f"{run_dir}|{arm}|{case_id}|{index}".encode()).hexdigest()[:10]


def build_queue(run_dir: str | Path, cases: list[CaseInput], case_ids: list[str] | None, arms: tuple[str, ...] = ARMS, seed: int = 7) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    outputs = load_outputs(run_dir, arms)
    by_id = {c.case_id: c for c in cases}
    wanted = set(case_ids) if case_ids is not None else set(by_id)
    rows: list[dict[str, Any]] = []
    key: dict[str, Any] = {}
    for arm in arms:
        for case_id, out in sorted((outputs.get(arm) or {}).items()):
            if case_id not in wanted or case_id not in by_id:
                continue
            case = by_id[case_id]
            for idx, it in enumerate(out.items):
                uid = _uid(Path(run_dir).name, arm, case_id, idx)
                rows.append({"item_uid": uid, "case_id": case_id, "presentation": case.presentation, "input_oneliner": case.oneliner,
                             "item_text": strip_formatting(it["text"]), "relevance": "", "safety": ""})
                key[uid] = {"arm": arm, "case_id": case_id, "item_index": idx, "record_id": it.get("record_id")}
    random.Random(seed).shuffle(rows)
    return rows, key


def export(run_dir: str | Path, cases: list[CaseInput], all_cases: bool = False, arms: tuple[str, ...] = ARMS, seed: int = 7) -> tuple[Path, Path]:
    run_dir = Path(run_dir)
    case_ids = None if all_cases else default_case_ids(cases)
    rows, key = build_queue(run_dir, cases, case_ids, arms, seed)
    csv_path, key_path = run_dir / "judging_queue.csv", run_dir / "judging_key.json"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    key_path.write_text(json.dumps({"_note": "SEALED: do not open while scoring judging_queue.csv", "seed": seed, "items": key}, indent=1))
    return csv_path, key_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--cases", default=None, help="benchmark glob/dir (default: benchmark/cases)")
    ap.add_argument("--all", action="store_true", help="every case x arm, not just the 12-case default")
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--allow-unfrozen", action="store_true")
    a = ap.parse_args(argv)
    cases = load_cases(a.cases, allow_unfrozen=a.allow_unfrozen)
    csv_path, key_path = export(a.run_dir, cases, a.all, tuple(a.arms.split(",")))
    print(f"queue: {csv_path}\nkey (sealed): {key_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
