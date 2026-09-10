from __future__ import annotations

from eval.item_parser import detect_citations, enrich, items_from_card, parse_free_text, split_items, strip_formatting

SAMPLE = """Given this presentation, here is what I would do:
**History:**
1. Ask about exertional onset and prodrome (Sheldon et al., 2002 found exertional syncope has LR+ 3.2 for cardiac cause).
2. Ask about family history of sudden death.
Physical examination:
- Auscultate for a late-peaking systolic murmur; sensitivity ~85% and specificity 60% for severe AS (JAMA 1997; PMID 9039886).
- Orthostatic vital signs at 1 and 3 minutes; check for a drop of 20 mmHg.
Tests:
- 12-lead ECG
- Echocardiogram (doi:10.1001/jama.277.7.564)
"""


def test_split_drops_headers_and_lead_in_keeps_bulleted_single_words():
    texts = [t for t, _ in split_items(SAMPLE)]
    assert texts[0].startswith("Ask about exertional onset")
    assert not any(t.lower().startswith("given") for t in texts)
    assert not any(t.rstrip(":").lower() in ("history", "physical examination", "tests") for t in texts)
    assert "12-lead ECG" in texts and any(t.startswith("Echocardiogram") for t in texts)
    assert len(texts) == 7


def test_header_context_and_evidence_clause_glued_to_item():
    items = parse_free_text(SAMPLE)
    ctx = {i.text[:12]: i.section for i in items}
    assert ctx["Ask about ex"] == "history" and ctx["Auscultate f"] == "exam" and ctx["12-lead ECG"] == "tests"
    murmur = next(i for i in items if i.text.startswith("Auscultate"))
    assert "sensitivity ~85%" in murmur.text  # the ';' evidence clause stayed with its item
    assert murmur.numeric_claims == ["1997", "60", "85", "9039886"]
    assert murmur.performance_claims == ["85", "60"]  # year excluded, order of appearance
    assert set(murmur.citations) == {"JAMA 1997", "PMID 9039886"}
    ortho = [i for i in items if "Orthostatic" in i.text or "drop of 20" in i.text]
    assert len(ortho) == 2  # a real second item after ';' is split off


def test_numbers_and_citations_detected():
    first = parse_free_text(SAMPLE)[0]
    assert first.numeric_claims == ["2002", "3.2"] and first.performance_claims == ["3.2"]
    assert first.citations == ["Sheldon et al., 2002"] and first.bedside and first.category == "history"
    echo = next(i for i in parse_free_text(SAMPLE) if i.text.startswith("Echocardiogram"))
    assert any(c.lower().startswith("doi:10.1001") for c in echo.citations) and echo.bedside is False
    assert detect_citations("as shown by Wells 1998 rule and (Simel 2009)") == ["(Simel 2009)"] or detect_citations("(Simel 2009)") == ["(Simel 2009)"]


def test_strip_formatting_and_enrich():
    assert strip_formatting("  3) **Check JVP**  ") == "Check JVP"
    assert strip_formatting("- • Ask about  chest pain.") == "Ask about chest pain."
    it = enrich("Orthostatic vitals", record_id="fn_orthostatic_vitals", section="examine")
    assert it.bedside and it.category == "functional" and it.section == "examine" and it.record_id == "fn_orthostatic_vitals"


def test_items_from_card_uses_rendered_numbers(index_db, records_by_id):
    from bedside_brief.render import render_card

    chosen = {"ask": [{"id": "hx_exertional_syncope", "rationale": "x"}], "examine": [{"id": "exam_late_peaking_murmur", "rationale": ""}]}
    card = render_card(chosen, records_by_id, {"presentation": "syncope", "chief_complaint": "s", "missing_features": []})
    items = items_from_card(card)
    assert [i.record_id for i in items] == ["hx_exertional_syncope", "exam_late_peaking_murmur"]
    assert all(i.bedside for i in items) and items[0].section == "ask" and items[1].section == "examine"
    assert "0.85" in items[0].numeric_claims and "0.85" in items[0].performance_claims and "1997" in items[0].numeric_claims
    assert items[0].citations and "Etchells" in items[0].citations[0]
