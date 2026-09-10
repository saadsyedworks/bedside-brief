"""Metrics on a tiny synthetic run with hand-computed expected values."""
from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from eval.arms import ArmOutput
from eval.cases import expand_case
from eval.item_parser import enrich
from eval.mapping import attach
from eval.metrics import compute_metrics, metrics_markdown, target_present, target_stratum, write_metrics
from tests.conftest import VERIFIED
from tests.test_eval_cases import TEMPLATE

LIMITS = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=False)
RECORDS = {r["identity"]["id"]: copy.deepcopy(r) for r in VERIFIED}
# targets of the template case: 0 murmur character (must), 1 prodrome question (must), 2 orthostatic vitals (not must)
TARGET_MAP = {"syncope_003": {0: ["exam_late_peaking_murmur"], 1: ["hx_syncope_prodrome"], 2: ["fn_orthostatic_vitals"]}}


def _item(text, record_id=None, section=None, numbers=None):
    it = enrich(text, record_id, section).to_dict()
    if numbers is not None:
        it["numeric_claims"] = numbers
        it["performance_claims"] = numbers
    return it


def _out(arm, case_id, items, ask_first=False, variant="base", error=None):
    return ArmOutput(arm=arm, case_id=case_id, base_case_id="syncope_003", variant=variant, model="fake", items=items, ask_first=ask_first, error=error)


@pytest.fixture
def cases():
    case = copy.deepcopy(TEMPLATE)
    case["perturbation_pair"]["expected_change_targets"] = [2]  # p1 must surface orthostatic vitals
    cs = expand_case(case, "t")
    attach(cs, TARGET_MAP)
    return cs


def test_target_presence_and_strata(cases):
    base = cases[0]
    out = _out("A", "syncope_003", [_item("Late-peaking systolic murmur", "exam_late_peaking_murmur", "examine")])
    titles = {i: r["identity"]["title"] for i, r in RECORDS.items()}
    assert target_present(base.targets[0], out, titles) == "id"
    assert target_present(base.targets[1], out, titles) is None
    c_out = _out("C", "syncope_003", [_item("Ask about any prodrome or palpitations before the event")])
    assert target_present(base.targets[1], c_out, titles) == "text"
    assert target_stratum(base.targets[0], RECORDS) == "quantified"
    assert target_stratum(base.targets[2], RECORDS) == "not_quantified"
    assert target_stratum(base.targets[1], RECORDS) == "unmapped"  # hx_syncope_prodrome not in the synthetic store


def test_metrics_hand_computed(cases, tmp_path):
    murmur = _item("Late-peaking systolic murmur", "exam_late_peaking_murmur", "examine", ["0.83", "0.72"])
    ortho = _item("Orthostatic vital signs", "fn_orthostatic_vitals", "examine", [])
    exertional = _item("Exertional syncope", "hx_exertional_syncope", "ask", ["0.85", "99"])  # 99 is NOT in the record -> fidelity miss
    A = {
        "syncope_003": _out("A", "syncope_003", [exertional, murmur]),
        "syncope_003_p1": _out("A", "syncope_003_p1", [exertional, murmur, ortho], variant="p1"),
        "syncope_003_n1": _out("A", "syncope_003_n1", [exertional, murmur], variant="n1"),
    }
    c_items = [
        _item("Ask about prodrome and palpitations before the event"),                       # history, bedside; matches target 1 by text
        _item("Carotid sinus massage (sensitivity 90%)", numbers=["90"]),                    # functional, bedside; SNR hit; 90 unsupported
        _item("Obtain a 12-lead ECG"),                                                        # ecg: off-bedside by default, bedside in ecg_bedside
        _item("Medication review (MAR)"),                                                     # mar: bedside by default, off in mar_offbedside
    ]
    C = {
        "syncope_003": _out("C", "syncope_003", c_items, ask_first=True),                    # ask-first false positive
        "syncope_003_p1": _out("C", "syncope_003_p1", c_items[:2], variant="p1"),            # no orthostatic vitals -> responsiveness 0
        "syncope_003_n1": _out("C", "syncope_003_n1", c_items[:2], variant="n1"),            # Jaccard 2/4
    }
    m = compute_metrics(cases, {"A": A, "C": C}, RECORDS, LIMITS, extracted_ids={"x", "y"})

    assert m["store"]["verified"] == 4 and m["store"]["extracted"] == 2 and m["store"]["not_quantified_share"] == 0.25
    cov = m["store"]["library_coverage"]
    assert (cov["targets"], cov["mapped_to_any_id"], cov["mapped_to_verified"]) == (3, 3, 2)
    assert m["cases"] == {"inputs": 3, "base": 1, "perturbation_pairs": 1, "noise_variants": 1, "underspecified": []}

    a = m["arms"]["A"]
    assert a["items_total"] == 7 and a["bedside_share"]["default"]["share"] == 1.0
    # must_have: 2 per input x 3 inputs = 6; murmur present in all three by id, prodrome never -> 3/6
    assert a["target_recall_must_have"]["present"] == 3 and a["target_recall_must_have"]["total"] == 6 and a["target_recall_must_have"]["recall"] == 0.5
    assert a["target_recall_must_have"]["found_by"] == {"id": 3}
    assert a["target_recall_must_have"]["strata"]["quantified"] == {"present": 3, "total": 3, "recall": 1.0}
    assert a["target_recall_must_have"]["strata"]["unmapped"] == {"present": 0, "total": 3, "recall": 0.0}
    assert a["target_recall_must_have"]["strata"]["not_quantified"]["total"] == 0
    # all targets: 3 per input; base 1/3, p1 2/3 (ortho by id), n1 1/3 -> 4/9
    assert a["target_recall_all"]["present"] == 4 and a["target_recall_all"]["total"] == 9
    # fidelity: displayed numbers 4 per input (0.85, 99, 0.83, 0.72) -> 3 matched each -> 9/12
    assert a["evidence_fidelity"] == {"matched": 9, "displayed": 12, "fidelity": 0.75}
    assert a["unsupported_claim_rate"]["unsupported"] == 3 and a["unsupported_claim_rate"]["claims"] == 12
    assert a["perturbation_responsiveness"] == {"pairs": 1, "rate": 1.0, "explicit_pairs": 1, "fallback_pairs": 0, "per_pair": {"syncope_003": {"score": 1.0, "how": "explicit"}}}
    assert a["noise_stability"]["jaccard_mean"] == 1.0 and a["brevity"]["pass_rate"] == 1.0
    assert a["should_not_recommend"]["cases_hit"] == 0 and a["ask_first"]["accuracy"] == 1.0

    c = m["arms"]["C"]
    assert c["items_total"] == 8 and c["evidence_fidelity"] is None
    # base: 3 of 4 bedside (ecg off); p1/n1: 2 of 2 -> 7/8 default; ecg_bedside 8/8; mar_offbedside 6/8
    assert c["bedside_share"]["default"]["bedside"] == 7 and c["bedside_share"]["ecg_bedside"]["share"] == 1.0 and c["bedside_share"]["mar_offbedside"]["bedside"] == 6
    assert c["bedside_share"]["default"]["per_case_mean"] == pytest.approx((0.75 + 1 + 1) / 3)
    assert c["target_recall_must_have"]["present"] == 3 and c["target_recall_must_have"]["found_by"] == {"text": 3}
    # numbers: "90" (carotid item) + "12" (12-lead ECG, auto-detected) in base; "90" again in p1 and n1 -> 4 claims, none backed
    assert c["unsupported_claim_rate"]["unsupported"] == 4 and c["unsupported_claim_rate"]["claims"] == 4 and c["unsupported_claim_rate"]["rate"] == 1.0
    assert c["unsupported_claim_rate"]["any_verified_record"]["unsupported"] == 4
    assert c["perturbation_responsiveness"]["rate"] == 0.0 and c["perturbation_responsiveness"]["explicit_pairs"] == 1
    assert c["noise_stability"]["jaccard_mean"] == 0.5
    assert c["should_not_recommend"]["cases_hit"] == 3 and c["should_not_recommend"]["examples"][0]["item"].startswith("Carotid sinus massage")
    assert c["ask_first"] == {"correct": 2, "cases": 3, "accuracy": pytest.approx(2 / 3), "false_positives": ["syncope_003"], "false_negatives": []}
    assert m["notes"] == []

    rows = [r for r in m["per_case"] if r["arm"] == "A" and r["case_id"] == "syncope_003"]
    assert rows[0]["missing_must_have"] == ["Ask: any prodrome, palpitations, or chest pain before event"] and rows[0]["must_have_present"] == 1
    pj, pm = write_metrics(m, tmp_path)
    assert pj.exists() and "| Target recall must_have | 50.0% | 50.0% |" in pm.read_text()
    assert "must_have recall [quantified] (n) | 100.0% (3)" in metrics_markdown(m)


def test_fallback_perturbation_and_errors(cases):
    for c in cases:
        c.expected_change_targets = []
    ortho = _item("Orthostatic vital signs", "fn_orthostatic_vitals", "examine")
    murmur = _item("Late-peaking systolic murmur", "exam_late_peaking_murmur", "examine")
    A = {"syncope_003": _out("A", "syncope_003", [murmur]), "syncope_003_p1": _out("A", "syncope_003_p1", [murmur, ortho], variant="p1"),
         "syncope_003_n1": _out("A", "syncope_003_n1", [], variant="n1", error="LLMError: boom")}
    m = compute_metrics(cases, {"A": A}, RECORDS, LIMITS)
    a = m["arms"]["A"]
    assert a["n_errors"] == 1 and a["errors"] == {"syncope_003_n1": "LLMError: boom"}
    assert a["perturbation_responsiveness"]["fallback_pairs"] == 1 and a["perturbation_responsiveness"]["rate"] == 1.0  # Jaccard change 0.5 >= 0.2
    assert a["perturbation_responsiveness"]["per_pair"]["syncope_003"]["how"].startswith("fallback_jaccard_change=0.50")
    assert a["noise_stability"]["jaccard_mean"] == 0.0 and any("fallback" in n for n in m["notes"])
    tight = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=1, MAX_POCUS=3, POCUS_ENABLED=False)
    assert compute_metrics(cases, {"A": A}, RECORDS, tight)["arms"]["A"]["brevity"]["pass"] == 2  # p1 has 2 examine items
