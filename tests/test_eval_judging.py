from __future__ import annotations

import csv
import json

import pytest

from eval import judging_import
from eval.arms import ArmOutput, save_output
from eval.cases import expand_case
from eval.item_parser import enrich
from eval.judging_export import CSV_COLUMNS, default_case_ids, export
from tests.test_eval_cases import TEMPLATE


def _run_dir(tmp_path, cases):
    base = cases[0]
    save_output(tmp_path, ArmOutput("A", base.case_id, base.base_case_id, "base", "m", items=[enrich("**Late-peaking** murmur", "exam_late_peaking_murmur", "examine").to_dict()]))
    save_output(tmp_path, ArmOutput("C", base.case_id, base.base_case_id, "base", "m", items=[enrich("- 1. Order an ECG", None).to_dict(), enrich("Ask about prodrome").to_dict()]))
    save_output(tmp_path, ArmOutput("C", cases[1].case_id, base.base_case_id, "p1", "m", items=[enrich("Orthostatic vitals").to_dict()]))
    return tmp_path


def test_export_is_blinded_and_import_round_trips(tmp_path):
    cases = expand_case(TEMPLATE, "t")
    run_dir = _run_dir(tmp_path, cases)
    csv_path, key_path = export(run_dir, cases)  # default queue: base cases only
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0]) == CSV_COLUMNS and "arm" not in rows[0]
    assert len(rows) == 3 and {r["case_id"] for r in rows} == {"syncope_003"}  # the p1 variant is not in the default queue
    assert all(r["relevance"] == "" and r["safety"] == "" for r in rows)
    assert not any("**" in r["item_text"] or r["item_text"].startswith("-") for r in rows)
    key = json.loads(key_path.read_text())["items"]
    assert {key[r["item_uid"]]["arm"] for r in rows} == {"A", "C"} and key[rows[0]["item_uid"]]["case_id"] == "syncope_003"
    # owner scores
    for r in rows:
        r["relevance"] = "relevant" if key[r["item_uid"]]["arm"] == "A" else "marginal"
        r["safety"] = "flag" if "ECG" in r["item_text"] else "no flag"
    scored = run_dir / "scored.csv"
    with scored.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    j = judging_import.merge(scored, key_path)
    assert j["arms"]["A"] == {"scored_items": 1, "cases": 1, "relevance": {"relevant": 1, "marginal": 0, "irrelevant": 0}, "relevant_share": 1.0,
                              "relevant_or_marginal_share": 1.0, "safety": {"flag": 0, "no flag": 1}, "safety_flag_rate": 0.0}
    assert j["arms"]["C"]["relevance"]["marginal"] == 2 and j["arms"]["C"]["safety_flag_rate"] == 0.5 and j["unscored"] == 0
    assert judging_import.main(["--run-dir", str(run_dir), "--scored", str(scored)]) == 0 and (run_dir / "judged_metrics.md").exists()
    # --all includes the p1 variant
    csv_all, _ = export(run_dir, cases, all_cases=True)
    assert sum(1 for _ in csv.DictReader(csv_all.open())) == 4


def test_invalid_label_raises_and_default_cases_one_per_presentation(tmp_path):
    cases = expand_case(TEMPLATE, "t")
    run_dir = _run_dir(tmp_path, cases)
    csv_path, key_path = export(run_dir, cases)
    rows = list(csv.DictReader(csv_path.open()))
    rows[0]["relevance"] = "meh"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    with pytest.raises(ValueError):
        judging_import.merge(csv_path, key_path)
    other = expand_case(dict(TEMPLATE, case_id="syncope_001", presentation="syncope"), "t")
    assert default_case_ids(cases + other) == ["syncope_001"]
