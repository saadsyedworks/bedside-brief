from __future__ import annotations

from types import SimpleNamespace

from bedside_brief import retrieve as rt


def ids(cands):
    return [c.id for c in cands]


def test_deterministic(index_db, parsed):
    first = rt.retrieve(parsed, index_db, pocus_enabled=True)
    second = rt.retrieve(parsed, index_db, pocus_enabled=True)
    assert first == second
    assert ids(first) == ids(second)


def test_primary_key_is_differentials(index_db, parsed):
    cands = rt.retrieve(parsed, index_db, pocus_enabled=True)
    assert all(c.matched_differentials for c in cands)
    assert set(ids(cands)) == {"hx_exertional_syncope", "exam_late_peaking_murmur", "fn_orthostatic_vitals", "pocus_ivc_collapsibility"}
    no_match = dict(parsed, differentials=[{"dx": "pneumonia", "weight": 1.0}])
    assert rt.retrieve(no_match, index_db, pocus_enabled=True) == []
    assert rt.retrieve(dict(parsed, differentials=[]), index_db) == []


def test_tag_boost_ordering(index_db, parsed):
    base = dict(parsed, differentials=[{"dx": "aortic_stenosis", "weight": 1.0}])
    exertional = rt.retrieve(dict(base, indication_tags=["exertional"]), index_db)
    assert ids(exertional)[:2] == ["hx_exertional_syncope", "exam_late_peaking_murmur"]
    assert exertional[0].score == 1.25 and exertional[0].matched_tags == ("exertional",)
    elderly = rt.retrieve(dict(base, indication_tags=["elderly"]), index_db)
    assert ids(elderly)[:2] == ["exam_late_peaking_murmur", "hx_exertional_syncope"]
    tie = rt.retrieve(dict(base, indication_tags=[]), index_db)
    assert ids(tie)[:2] == ["exam_late_peaking_murmur", "hx_exertional_syncope"]  # tie -> id order


def test_presentation_filter_with_cross_presentation_fallback(index_db, parsed):
    dizzy = dict(parsed, presentation="dizziness")
    cands = rt.retrieve(dizzy, index_db)
    assert ids(cands)[0] == "fn_orthostatic_vitals"  # in-presentation first despite lower score
    assert cands[0].cross_presentation is False
    assert all(c.cross_presentation for c in cands[1:])
    assert ids(cands)[1:] == ["hx_exertional_syncope", "exam_late_peaking_murmur"]  # tag boost breaks the tie


def test_pocus_excluded_unless_enabled(index_db, parsed, monkeypatch):
    import config

    assert "pocus_ivc_collapsibility" not in ids(rt.retrieve(parsed, index_db, pocus_enabled=False))
    assert "pocus_ivc_collapsibility" in ids(rt.retrieve(parsed, index_db, pocus_enabled=True))
    monkeypatch.setattr(config, "POCUS_ENABLED", False)
    assert "pocus_ivc_collapsibility" not in ids(rt.retrieve(parsed, index_db))


def test_fixed_order_respects_limits(index_db, parsed):
    limits = SimpleNamespace(MAX_ASK=1, MAX_EXAMINE=1, MAX_POCUS=1)
    sections = rt.retrieve_fixed_order(parsed, index_db, pocus_enabled=True, limits=limits)
    assert set(sections) == {"ask", "examine", "pocus"}
    assert ids(sections["ask"]) == ["hx_exertional_syncope"]
    assert ids(sections["examine"]) == ["exam_late_peaking_murmur"]  # fn truncated away
    assert ids(sections["pocus"]) == ["pocus_ivc_collapsibility"]
    disabled = rt.retrieve_fixed_order(parsed, index_db, pocus_enabled=False)
    assert "pocus" not in disabled and ids(disabled["examine"]) == ["exam_late_peaking_murmur", "fn_orthostatic_vitals"]
    chosen = rt.to_chosen(sections)
    assert chosen["ask"] == [{"id": "hx_exertional_syncope", "rationale": ""}]
