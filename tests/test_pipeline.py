from __future__ import annotations

import re
from types import SimpleNamespace

from bedside_brief import pipeline
from bedside_brief.llm import FakeLLM
from bedside_brief.validate import validate_card

PARSE = {
    "chief_complaint": "65M syncope on stairs",
    "presentation": "syncope",
    "time_course": "acute",
    "modifiers": ["exertional"],
    "differentials": [
        {"dx": "aortic_stenosis", "weight": 1.0},
        {"dx": "orthostatic_hypotension", "weight": 0.5},
        {"dx": "hypovolemic_hemorrhagic_shock", "weight": 0.5},
    ],
    "indication_tags": ["exertional"],
    "missing_features": [],
}
RANK = {
    "ask": [{"id": "hx_exertional_syncope", "rationale": "Exertional onset."}],
    "examine": [{"id": "exam_late_peaking_murmur", "rationale": "Murmur character."}, {"id": "fn_orthostatic_vitals", "rationale": ""}],
    "pocus": [],
}
ALL = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=True)


def test_end_to_end_card_validates(index_db, records_by_id):
    llm = FakeLLM([PARSE, dict(RANK, pocus=[{"id": "pocus_ivc_collapsibility", "rationale": "Volume."}])])
    out = pipeline.brief("65M syncope on stairs", llm, index_db, ALL)
    assert set(out) == {"parsed", "candidates", "chosen", "card", "validation"}
    assert out["parsed"]["chief_complaint"] == "[n]M syncope on stairs"
    assert set(out["candidates"]) == {"hx_exertional_syncope", "exam_late_peaking_murmur", "fn_orthostatic_vitals", "pocus_ivc_collapsibility"}
    assert out["validation"]["ok"] is True and "blocked" not in out["card"]
    assert [i["id"] for i in out["card"]["sections"]["ask"]] == ["hx_exertional_syncope"]
    assert [i["id"] for i in out["card"]["sections"]["pocus"]] == ["pocus_ivc_collapsibility"]
    assert validate_card(out["card"], records_by_id).ok
    assert len(llm.calls) == 2  # parser then ranker, nothing else


def test_llm_number_in_rationale_is_stripped_and_card_still_validates(index_db, records_by_id):
    rank = dict(RANK, ask=[{"id": "hx_exertional_syncope", "rationale": "Strong: LR+ 4.2 for AS."}])
    out = pipeline.brief("65M syncope on stairs", FakeLLM([PARSE, rank]), index_db)
    item = out["card"]["sections"]["ask"][0]
    assert item["rationale"] == "Strong: LR+ [n].[n] for AS."
    assert not re.search(r"\d", item["rationale"])
    assert out["validation"]["ok"] is True and "blocked" not in out["card"]
    assert "pocus" not in out["card"]["sections"]  # config default: disabled
    assert "pocus_ivc_collapsibility" not in out["candidates"]


def test_missing_features_surface_as_ask_first(index_db):
    parse = dict(PARSE, missing_features=["exertional vs positional", "BP at 3 min?"])
    out = pipeline.brief("syncope", FakeLLM([parse, RANK]), index_db)
    assert out["card"]["ask_first"] == ["exertional vs positional", "BP at [n] min?"]
    assert out["validation"]["ok"] is True
