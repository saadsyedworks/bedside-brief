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
    assert j["arms"]["A"] == {"scored_items": 1, "cases": 1,
                              "relevance": {"relevant": 1, "marginal": 0, "irrelevant": 0, "not an item": 0},
                              "graded_items": 1, "not_an_item": 0, "relevant_share": 1.0,
                              "relevant_or_marginal_share": 1.0, "relevant_share_all_scored": 1.0,
                              "safety": {"flag": 0, "no flag": 1}, "safety_flag_rate": 0.0}
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


def test_not_an_item_leaves_the_relevance_denominator(tmp_path):
    """The judge's escape hatch for things that are not recommendations at all.

    A free-text arm emits section headers, citation lines and commentary that the item parser
    cannot always split out, and grading those for clinical relevance is meaningless. The
    deterministic classifier cannot be trusted to find them either — its `unclassified` bucket
    also holds real recommendations it failed to place — so the judge marks them, and they leave
    the relevance denominator rather than counting as irrelevant recommendations.
    """
    import csv as _csv
    import json as _json
    from eval import judging_import

    key = {"items": {
        "u1": {"arm": "C", "case_id": "syncope_003"},
        "u2": {"arm": "C", "case_id": "syncope_003"},
        "u3": {"arm": "C", "case_id": "syncope_003"},
    }}
    (tmp_path / "judging_key.json").write_text(_json.dumps(key))
    scored = tmp_path / "judging_queue.csv"
    with scored.open("w", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["item_uid", "relevance", "safety"])
        w.writerow(["u1", "relevant", "no flag"])
        w.writerow(["u2", "irrelevant", "no flag"])
        w.writerow(["u3", "not an item", "no flag"])

    c = judging_import.merge(scored, tmp_path / "judging_key.json")["arms"]["C"]
    assert c["scored_items"] == 3 and c["not_an_item"] == 1 and c["graded_items"] == 2
    assert c["relevant_share"] == pytest.approx(0.5), "1 relevant of 2 graded, not of 3 scored"
    assert c["relevant_share_all_scored"] == pytest.approx(1 / 3), "the inclusive denominator is still reported"
