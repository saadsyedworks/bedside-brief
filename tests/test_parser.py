from __future__ import annotations

import re

import pytest

import config
from bedside_brief import parser as ps
from bedside_brief.llm import FakeLLM

GOOD = {
    "chief_complaint": "65M syncope climbing 2 flights of stairs",
    "presentation": "syncope",
    "time_course": "acute, within 24 hours",
    "modifiers": ["exertional", "BP 90/60 on arrival"],
    "differentials": [{"dx": "aortic_stenosis", "weight": 0.8}, {"dx": "orthostatic_hypotension", "weight": 0.4}],
    "indication_tags": ["exertional", "elderly"],
    "missing_features": ["was BP < 90 at onset?"],
    "underspecified": True,
}


def test_parses_and_strips_digits_from_every_free_text_field():
    llm = FakeLLM(GOOD)
    parsed = ps.parse_oneliner("65M with syncope on stairs", llm)
    assert parsed["presentation"] == "syncope"
    assert parsed["indication_tags"] == ["exertional", "elderly"]
    for field in ("chief_complaint", "time_course"):
        assert not re.search(r"\d", parsed[field]), field
    for field in ("modifiers", "missing_features"):
        assert all(not re.search(r"\d", s) for s in parsed[field]), field
    assert parsed["chief_complaint"] == "[n]M syncope climbing [n] flights of stairs"
    assert parsed["missing_features"] == ["was BP < [n] at onset?"]
    # the prompt embeds the vocab and forbids other numbers
    system = llm.calls[0]["system"]
    assert "aortic_stenosis" in system and "exertional" in system and "ONLY" in system
    assert "missing_features" in system


def test_weights_normalised_descending_top_is_one():
    reply = dict(GOOD, differentials=[
        {"dx": "orthostatic_hypotension", "weight": 0.2},
        {"dx": "aortic_stenosis", "weight": 0.8},
        {"dx": "aortic_stenosis", "weight": 0.5},  # duplicate: keep the highest
        {"dx": "hcm", "weight": 1.7},  # clamped to 1.0
    ])
    parsed = ps.parse_oneliner("x", FakeLLM(reply))
    weights = [d["weight"] for d in parsed["differentials"]]
    assert [d["dx"] for d in parsed["differentials"]] == ["hcm", "aortic_stenosis", "orthostatic_hypotension"]
    assert weights == sorted(weights, reverse=True) and weights[0] == 1.0
    assert all(0.0 <= w <= 1.0 for w in weights)


def test_differentials_truncated_to_max():
    dxs = ["aortic_stenosis", "hcm", "reflex_vasovagal", "orthostatic_hypotension", "bradyarrhythmia", "tachyarrhythmia", "pulmonary_embolism", "seizure_mimic"]
    reply = dict(GOOD, differentials=[{"dx": d, "weight": 1.0 - i * 0.1} for i, d in enumerate(dxs)])
    parsed = ps.parse_oneliner("x", FakeLLM(reply))
    assert len(parsed["differentials"]) == config.MAX_DIFFERENTIALS
    assert [d["dx"] for d in parsed["differentials"]] == dxs[: config.MAX_DIFFERENTIALS]


@pytest.mark.parametrize("field, value", [
    ("presentation", "fainting"),
    ("differentials", [{"dx": "aortic_stenosis", "weight": 1.0}, {"dx": "vasovagal", "weight": 0.5}]),
    ("indication_tags", ["exertional", "on_stairs"]),
])
def test_out_of_vocab_raises_not_dropped(field, value):
    with pytest.raises(ps.ParserVocabError) as exc:
        ps.parse_oneliner("x", FakeLLM(dict(GOOD, **{field: value})))
    assert "vocab" in str(exc.value)


def test_no_differentials_is_a_contract_error():
    with pytest.raises(ps.ParserError):
        ps.parse_oneliner("x", FakeLLM(dict(GOOD, differentials=[])))
    with pytest.raises(ps.ParserError):
        ps.parse_oneliner("   ", FakeLLM(GOOD))
