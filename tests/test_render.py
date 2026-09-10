from __future__ import annotations

import re
from types import SimpleNamespace

from bedside_brief import render
from bedside_brief.validate import normalise_number

CHROME_KEYS = {"rationale", "audit_link"}  # the only item strings not copied verbatim from the record


def record_leaves(record) -> set[str]:
    out: set[str] = set()

    def walk(node):
        if isinstance(node, bool) or node is None:
            return
        if isinstance(node, (int, float)):
            out.add(normalise_number(node))
        elif isinstance(node, str):
            out.add(node)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(record)
    return out


def item_leaves(item):
    for key, value in item.items():
        if key in CHROME_KEYS:
            continue
        if isinstance(value, list):
            for est in value:
                for k2, v2 in est.items():
                    if isinstance(v2, dict):
                        yield from ((f"{k2}.{k3}", v3) for k3, v3 in v2.items())
                    else:
                        yield k2, v2
        else:
            yield key, value


def chosen_for(records_by_id, pocus=True):
    chosen = {
        "ask": [{"id": "hx_exertional_syncope", "rationale": "Exertional onset points to AS in 65-year-olds (LR+ 2.1)."}],
        "examine": [{"id": "exam_late_peaking_murmur", "rationale": "Murmur character."}, {"id": "fn_orthostatic_vitals", "rationale": ""}],
    }
    if pocus:
        chosen["pocus"] = [{"id": "pocus_ivc_collapsibility", "rationale": "Volume status."}]
    return chosen


def test_card_built_only_from_stored_fields(records_by_id, parsed):
    limits = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=True)
    card = render.render_card(chosen_for(records_by_id), records_by_id, parsed, limits)
    assert set(card["sections"]) == {"ask", "examine", "pocus"}
    for items in card["sections"].values():
        for item in items:
            allowed = record_leaves(records_by_id[item["id"]])
            for key, value in item_leaves(item):
                if value is None or isinstance(value, bool):
                    continue
                assert value in allowed, f"{item['id']}.{key}={value!r} is not a stored field"
            assert item["audit_link"] == f"/record/{item['id']}"
    exam = card["sections"]["examine"][0]
    assert exam["evidence_badge"] == "quantified" and len(exam["evidence"]) == 2  # two populations, never averaged
    assert exam["evidence"][0]["sensitivity"] == {"value": "0.83", "ci_low": "0.75", "ci_high": "0.89"}
    assert exam["evidence"][0]["pmid"] == "9039886" and exam["evidence"][0]["year"] == "1997"
    fn = card["sections"]["examine"][1]
    assert fn["evidence_badge"] == "not_quantified" and fn["evidence"] == []


def test_rationale_digits_stripped(records_by_id, parsed):
    limits = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=True)
    card = render.render_card(chosen_for(records_by_id), records_by_id, parsed, limits)
    rationale = card["sections"]["ask"][0]["rationale"]
    assert not re.search(r"\d", rationale)
    assert rationale == "Exertional onset points to AS in [n]-year-olds (LR+ [n].[n])."
    assert render.strip_numbers(None) == ""


def test_ask_first_present_only_when_missing_features(records_by_id, parsed):
    card = render.render_card(chosen_for(records_by_id, pocus=False), records_by_id, parsed)
    assert "ask_first" not in card
    parsed2 = dict(parsed, missing_features=["exertional vs positional onset", "BP < 90 at onset?"], underspecified=True, chief_complaint="65M syncope")
    card2 = render.render_card(chosen_for(records_by_id, pocus=False), records_by_id, parsed2)
    assert card2["ask_first"] == ["exertional vs positional onset", "BP < [n] at onset?"]
    assert card2["chief_complaint"] == "[n]M syncope"


def test_limits_enforced_and_pocus_dropped_when_disabled(records_by_id, parsed):
    chosen = chosen_for(records_by_id)
    tight = SimpleNamespace(MAX_ASK=1, MAX_EXAMINE=1, MAX_POCUS=1, POCUS_ENABLED=False)
    card = render.render_card(chosen, records_by_id, parsed, tight)
    assert "pocus" not in card["sections"]
    assert [i["id"] for i in card["sections"]["examine"]] == ["exam_late_peaking_murmur"]
    default = render.render_card(chosen, records_by_id, parsed)  # config: POCUS_ENABLED False
    assert "pocus" not in default["sections"]


def test_unverified_or_wrong_section_ids_skipped(records_by_id, parsed):
    chosen = {
        "ask": [{"id": "hx_positional_vertigo", "rationale": "extracted only"}, {"id": "ghost_id", "rationale": ""},
                {"id": "exam_late_peaking_murmur", "rationale": "exam in ask section"}],
        "examine": [{"id": "hx_exertional_syncope", "rationale": "history in examine"}],
    }
    card = render.render_card(chosen, records_by_id, parsed)
    assert card["sections"]["ask"] == [] and card["sections"]["examine"] == []


def test_html_has_sections_copy_line_and_digit_free_chrome(records_by_id, parsed):
    empty = {"presentation": "syncope", "chief_complaint": "", "sections": {"ask": [], "examine": []}}
    html = render.render_html(empty)
    visible = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    assert not re.search(r"\d", visible), visible
    assert render.COPY_LINE in html and "ASK" in html and "EXAMINE" in html and "POCUS" not in html
    limits = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=True)
    full = render.render_html(render.render_card(chosen_for(records_by_id), records_by_id, dict(parsed, missing_features=["onset"], underspecified=True), limits), oneliner="x")
    assert "<details>" in full and "Late-peaking systolic murmur" in full and "Ask first" in full and "POCUS" in full
    assert "0.83" in full and "CI 0.75–0.89" in full and "/record/exam_late_peaking_murmur" in full
