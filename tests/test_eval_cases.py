from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from eval.cases import FreezeError, by_base, expand_case, load_cases

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = {k: v for k, v in json.loads((ROOT / "benchmark_case_template.json").read_text()).items() if not k.startswith("_")}


def _write(tmp_path: Path, case: dict, name: str | None = None) -> Path:
    p = tmp_path / f"{name or case['case_id']}.json"
    p.write_text(json.dumps(case))
    return p


def test_expand_case_shares_metadata_and_suffixes():
    inputs = expand_case(TEMPLATE, "template")
    assert [c.variant for c in inputs] == ["base", "p1", "n1"]
    assert [c.case_id for c in inputs] == ["syncope_003", "syncope_003_p1", "syncope_003_n1"]
    assert all(c.base_case_id == "syncope_003" and c.presentation == "syncope" for c in inputs)
    assert all(len(c.targets) == 3 and len(c.must_have_targets) == 2 for c in inputs)
    assert all(c.should_not_recommend == TEMPLATE["should_not_recommend"] for c in inputs)
    assert inputs[1].expected_change.startswith("Orthostatic vitals becomes") and inputs[2].expected_change.startswith("None")
    assert inputs[0].oneliner != inputs[1].oneliner != inputs[2].oneliner
    assert by_base(inputs)["syncope_003"]["p1"] is inputs[1]


def test_underspecified_flag_clears_on_p1_when_authors_say_so():
    case = copy.deepcopy(TEMPLATE)
    case["underspecified_flag_expected"] = True
    case["perturbation_pair"]["expected_change"] = "Underspecified flag should clear enough to rank; ..."
    base, p1, n1 = expand_case(case, "x")
    assert base.underspecified_expected and n1.underspecified_expected and not p1.underspecified_expected
    case["perturbation_pair"]["expected_change"] = "Still vague."
    assert expand_case(case, "x")[1].underspecified_expected


def test_expected_change_targets_from_case_field_or_sidecar():
    case = copy.deepcopy(TEMPLATE)
    assert expand_case(case, "x")[1].expected_change_targets == []
    assert expand_case(case, "x", {"syncope_003": [2, "fn_orthostatic_vitals"]})[1].expected_change_targets == [2, "fn_orthostatic_vitals"]
    case["perturbation_pair"]["expected_change_targets"] = [2]
    assert expand_case(case, "x", {"syncope_003": [0]})[1].expected_change_targets == [2]  # case field wins


def test_freeze_protocol(tmp_path):
    _write(tmp_path, TEMPLATE)  # frozen_commit == ""
    with pytest.raises(FreezeError):
        load_cases(tmp_path)
    assert len(load_cases(tmp_path, allow_unfrozen=True)) == 3
    frozen = dict(TEMPLATE, frozen_commit="abc123", case_id="syncope_004")
    frozen["perturbation_pair"] = dict(frozen["perturbation_pair"], case_id="syncope_004_p1")
    frozen["noise_variant"] = dict(frozen["noise_variant"], case_id="syncope_004_n1")
    only = tmp_path / "frozen"
    only.mkdir()
    _write(only, frozen)
    assert [c.case_id for c in load_cases(str(only / "*.json"))] == ["syncope_004", "syncope_004_p1", "syncope_004_n1"]
    with pytest.raises(FileNotFoundError):
        load_cases(tmp_path / "nothing")
