from __future__ import annotations

import json
import re
from types import SimpleNamespace

import pytest

from bedside_brief import rank as rk
from bedside_brief import retrieve as rt
from bedside_brief.llm import FakeLLM

ALL = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=True)
NO_POCUS = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=4, MAX_POCUS=3, POCUS_ENABLED=False)


def choice(ask=(), examine=(), pocus=()):
    return {s: [{"id": i, "rationale": f"because {i}"} for i in ids] for s, ids in (("ask", ask), ("examine", examine), ("pocus", pocus))}


@pytest.fixture
def candidates(index_db, parsed):
    return rt.retrieve(parsed, index_db, pocus_enabled=True)


def test_happy_path_returns_chosen_contract(candidates, parsed):
    llm = FakeLLM(choice(["hx_exertional_syncope"], ["exam_late_peaking_murmur", "fn_orthostatic_vitals"], ["pocus_ivc_collapsibility"]))
    chosen = rk.rank(parsed, candidates, llm, ALL)
    assert set(chosen) == {"ask", "examine", "pocus"}
    assert chosen["ask"] == [{"id": "hx_exertional_syncope", "rationale": "because hx_exertional_syncope"}]
    assert [c["id"] for c in chosen["examine"]] == ["exam_late_peaking_murmur", "fn_orthostatic_vitals"]


def test_foreign_id_is_containment_error(candidates, parsed):
    with pytest.raises(rk.RankerContainmentError):
        rk.rank(parsed, candidates, FakeLLM(choice(["hx_made_up"])), ALL)
    with pytest.raises(rk.RankerContainmentError):  # real record, but not retrieved
        rk.rank(parsed, candidates, FakeLLM(choice(["hx_positional_vertigo"])), ALL)


def test_type_section_mismatch_is_containment_error(candidates, parsed):
    with pytest.raises(rk.RankerContainmentError):
        rk.rank(parsed, candidates, FakeLLM(choice(ask=["exam_late_peaking_murmur"])), ALL)
    with pytest.raises(rk.RankerContainmentError):
        rk.rank(parsed, candidates, FakeLLM(choice(examine=["hx_exertional_syncope"])), ALL)
    with pytest.raises(rk.RankerContainmentError):
        rk.rank(parsed, candidates, FakeLLM(choice(examine=["pocus_ivc_collapsibility"])), ALL)


def test_limits_enforced_in_llm_order(candidates, parsed):
    tight = SimpleNamespace(MAX_ASK=4, MAX_EXAMINE=1, MAX_POCUS=3, POCUS_ENABLED=True)
    llm = FakeLLM(choice(examine=["fn_orthostatic_vitals", "exam_late_peaking_murmur"]))
    chosen = rk.rank(parsed, candidates, llm, tight)
    assert [c["id"] for c in chosen["examine"]] == ["fn_orthostatic_vitals"]  # LLM order kept, then truncated
    dup = FakeLLM(choice(examine=["fn_orthostatic_vitals", "fn_orthostatic_vitals"]))
    assert len(rk.rank(parsed, candidates, dup, ALL)["examine"]) == 1


def test_pocus_dropped_when_disabled(index_db, parsed):
    cands = rt.retrieve(parsed, index_db, pocus_enabled=False)
    llm = FakeLLM(choice(["hx_exertional_syncope"], ["exam_late_peaking_murmur"], ["pocus_ivc_collapsibility"]))
    chosen = rk.rank(parsed, cands, llm, NO_POCUS)
    assert "pocus" not in chosen and set(chosen) == {"ask", "examine"}
    assert "pocus must be an empty list" in llm.calls[0]["system"]


def test_rationale_digits_stripped(candidates, parsed):
    reply = {"ask": [{"id": "hx_exertional_syncope", "rationale": "LR+ 2.1 in 65-year-olds"}], "examine": [], "pocus": []}
    chosen = rk.rank(parsed, candidates, FakeLLM(reply), ALL)
    assert chosen["ask"][0]["rationale"] == "LR+ [n].[n] in [n]-year-olds"


def test_prompt_carries_no_estimate_numbers(candidates, parsed):
    llm = FakeLLM(choice(["hx_exertional_syncope"]))
    rk.rank(parsed, candidates, llm, ALL)
    user = llm.calls[0]["user"]
    payload = json.loads(user)
    assert {c.id for c in candidates} == {r["id"] for r in payload["candidates"]}
    assert set(payload["candidates"][0]) == {"id", "title", "type", "changes_what", "evidence_status"}
    # every digit in the prompt must be a differential weight or the parsed summary, never a candidate field
    candidate_text = json.dumps(payload["candidates"])
    assert not re.search(r"\d", candidate_text), candidate_text
    for token in ("0.85", "85", "2.1", "9039886", "1997", "Etchells", "JAMA", "sensitivity", "citation"):
        assert token not in user, token
    assert "aortic_stenosis" in user  # the parsed summary is present


def test_candidate_summary_guard_raises_on_leak(candidates, monkeypatch):
    monkeypatch.setattr(rk, "strip_numbers", lambda s: s or "")  # disable stripping
    leaky = candidates[0].record
    monkeypatch.setitem(leaky["interpretation"], "changes_what", "LR+ 2.1 changes the plan")
    with pytest.raises(rk.RankerNumberLeak):
        rk.candidate_summary(candidates)


def test_arrow_in_changes_what_is_not_a_leaked_number(candidates):
    """An arrow escapes to \\u2192 under json.dumps' default, which the scan reads as 2192.

    Ten verified records write "finding -> action" with a real arrow, so a guard that serialises
    with ensure_ascii=True rejects every card that retrieves one of them.
    """
    rec = candidates[0].record
    rec["interpretation"]["changes_what"] = "a full bladder \u2192 catheterise before imaging"
    rec["identity"]["title"] = "Bladder percussion \u2014 dullness above the pubis"
    rows = rk.candidate_summary(candidates)
    assert "\u2192" in rows[0]["changes_what"]


def test_no_candidates_skips_llm(parsed):
    llm = FakeLLM(choice())
    assert rk.rank(parsed, [], llm, NO_POCUS) == {"ask": [], "examine": []}
    assert llm.calls == []
