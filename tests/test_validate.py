from __future__ import annotations

import copy
from types import SimpleNamespace

from bedside_brief import render, validate
from bedside_brief.validate import normalise_number, scan_numbers

LIMITS = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=True)


def good_card(records_by_id, parsed):
    chosen = {
        "ask": [{"id": "hx_exertional_syncope", "rationale": "LR+ 2.1 here"}],
        "examine": [{"id": "exam_late_peaking_murmur", "rationale": ""}, {"id": "fn_orthostatic_vitals", "rationale": ""}],
        "pocus": [{"id": "pocus_ivc_collapsibility", "rationale": ""}],
    }
    return render.render_card(chosen, records_by_id, parsed, LIMITS)


def test_scan_numbers_forms():
    assert scan_numbers("sens 0.85, spec 60%, LR+ 4.2, range 0.7–0.9 or 0.7-0.9, n=1200") == {"0.85", "60", "4.2", "0.7", "0.9", "1200"}
    assert scan_numbers("Table 2; .85; 2.10") == {"2", "0.85", "2.1"}
    assert scan_numbers("no digits here") == set()
    assert normalise_number(0.85) == "0.85" and normalise_number("85%") == "85" and normalise_number(2.0) == "2"
    assert normalise_number("+4.20") == "4.2" and normalise_number("abc") == "abc"


def test_matching_card_passes(records_by_id, parsed):
    result = validate.validate_card(good_card(records_by_id, parsed), records_by_id)
    assert result.ok and result.violations == [] and result.bad_item_ids == []


def test_number_not_in_linked_record_is_blocked(records_by_id, parsed):
    card = good_card(records_by_id, parsed)
    card["sections"]["examine"][0]["how"] += " Sensitivity 99% in one study."  # 99 exists in no record
    result = validate.validate_card(card, records_by_id)
    assert not result.ok
    assert result.bad_item_ids == ["exam_late_peaking_murmur"]
    assert any("99" in v for v in result.violations)
    blocked = validate.block(card, result)
    assert [i["id"] for i in blocked["sections"]["examine"]] == ["fn_orthostatic_vitals"]
    assert blocked["blocked"]["removed"] == ["exam_late_peaking_murmur"]
    assert len(blocked["sections"]["ask"]) == 1  # untouched items survive
    assert validate.validate_card(blocked, records_by_id).ok
    replaced, res2 = validate.validate_or_block(card, records_by_id)
    assert replaced == blocked and not res2.ok


def test_number_from_another_linked_record_still_fails_per_item(records_by_id, parsed):
    card = good_card(records_by_id, parsed)
    card["sections"]["ask"][0]["how"] += " see 4.4"  # 4.4 belongs to the exam record, not the history one
    result = validate.validate_card(card, records_by_id)
    assert not result.ok and result.bad_item_ids == ["hx_exertional_syncope"]


def test_card_level_number_must_come_from_a_linked_record(records_by_id, parsed):
    card = good_card(records_by_id, parsed)
    card["ask_first"] = ["ask about 0.83"]  # present in a linked record -> allowed
    assert validate.validate_card(card, records_by_id).ok
    card["ask_first"] = ["ask about 123456"]
    result = validate.validate_card(card, records_by_id)
    assert not result.ok and result.bad_item_ids == [] and "card:" in result.violations[0]


def test_item_id_not_verified_is_violation(records_by_id, parsed):
    card = good_card(records_by_id, parsed)
    extracted = copy.deepcopy(records_by_id["hx_exertional_syncope"])
    extracted["tier"] = "extracted"
    extracted["identity"]["id"] = "hx_positional_vertigo"
    everything = dict(records_by_id, hx_positional_vertigo=extracted)
    card["sections"]["ask"].append(render.render_item(extracted, ""))
    card["sections"]["ask"].append({"id": "ghost_id", "title": "x", "evidence": []})
    result = validate.validate_card(card, everything)
    assert not result.ok
    assert result.bad_item_ids == ["hx_positional_vertigo", "ghost_id"]
    assert all("not a verified record" in v for v in result.violations)
    blocked = validate.block(card, result)
    assert [i["id"] for i in blocked["sections"]["ask"]] == ["hx_exertional_syncope"]


def test_violations_logged(records_by_id, parsed, caplog):
    card = good_card(records_by_id, parsed)
    card["sections"]["ask"][0]["title"] = "Version 77"
    with caplog.at_level("WARNING", logger="bedside_brief.validate"):
        validate.validate_card(card, records_by_id)
    assert any("validator" in r.message and "77" in r.message for r in caplog.records)
