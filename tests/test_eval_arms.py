from __future__ import annotations

import json

from bedside_brief.llm import FakeLLM
from eval.arms import ArmOutput, C_SCHEMA, GENERIC_PROMPT, load_outputs, run_arm, run_arm_a, run_arm_b, run_arm_c, run_case_arm, write_manifest
from eval.cases import expand_case
from tests.test_eval_cases import TEMPLATE
from tests.test_pipeline import PARSE, RANK

C_TEXT = "History:\n1. Ask about exertional onset (sensitivity 85%, Etchells et al., 1997).\nExam:\n- Orthostatic vitals\n- Late-peaking murmur, LR+ 12.7\nTests:\n- ECG\n- Echocardiogram\n"


def _llm():
    def reply(system, user, schema):
        return {"oneliner_parse": PARSE, "card_choice": RANK, "free_text_answer": {"answer": C_TEXT}}[schema["title"]]
    return FakeLLM(reply)


def test_three_arms_produce_arm_output(index_db):
    case = expand_case(TEMPLATE, "t")[0]
    a, b, c = run_arm_a(case, _llm(), index_db), run_arm_b(case, _llm(), index_db), run_arm_c(case, _llm())
    for out, arm in ((a, "A"), (b, "B"), (c, "C")):
        assert isinstance(out, ArmOutput) and out.arm == arm and out.case_id == "syncope_003" and out.error is None
        assert set(out.to_dict()) >= {"arm", "case_id", "items", "raw", "ask_first", "blocked_items"}
        for it in out.items:
            assert set(it) >= {"text", "record_id", "section", "bedside", "numeric_claims", "citations"}
    assert a.record_ids == ["hx_exertional_syncope", "exam_late_peaking_murmur", "fn_orthostatic_vitals"] and a.items[0]["section"] == "ask"
    assert a.raw["validation"]["ok"] and a.blocked_items == [] and a.ask_first is False
    # B: fixed retrieval order, no ranker call
    assert set(b.record_ids) == {"hx_exertional_syncope", "exam_late_peaking_murmur", "fn_orthostatic_vitals"}
    assert [i["section"] for i in b.items] == ["ask", "examine", "examine"]
    # C: verbatim prompt, raw text kept, parsed items without ids
    assert c.raw["prompt"] == GENERIC_PROMPT and c.raw["text"] == C_TEXT
    assert all(i["record_id"] is None for i in c.items) and len(c.items) == 5
    assert [i["bedside"] for i in c.items] == [True, True, True, False, False]
    assert c.items[2]["numeric_claims"] == ["12.7"] and c.items[0]["citations"] == ["Etchells et al., 1997"]


def test_arm_c_prompt_is_verbatim_and_only_one_call(index_db):
    case = expand_case(TEMPLATE, "t")[0]
    llm = _llm()
    run_arm_c(case, llm)
    assert len(llm.calls) == 1 and llm.calls[0]["user"].startswith(GENERIC_PROMPT) and case.oneliner in llm.calls[0]["user"]
    assert llm.calls[0]["schema"] is C_SCHEMA
    ask = run_arm_c(case, FakeLLM({"answer": "I would need more information before I can rank anything."}))
    assert ask.ask_first is True and ask.items == []


def test_arm_b_calls_parser_only(index_db):
    case = expand_case(TEMPLATE, "t")[0]
    llm = _llm()
    run_arm_b(case, llm, index_db)
    assert len(llm.calls) == 1 and llm.calls[0]["schema"]["title"] == "oneliner_parse"


def test_errors_are_captured_not_raised(index_db):
    case = expand_case(TEMPLATE, "t")[0]
    bad = FakeLLM(dict(PARSE, differentials=[{"dx": "not_in_vocab", "weight": 1.0}]))
    out = run_arm("A", case, bad, index_db)
    assert out.error and "ParserVocabError" in out.error and out.items == []


def test_resume_retries_a_stored_failure(index_db, tmp_path):
    """A failed case must not be resumable as a finished empty card.

    run_arm never raises, so a blown-up case is saved with `error` set and no items. If resume
    treated that file as done, a transient failure — or one the code was since fixed for — would
    be counted as a real empty card in the reported metrics.
    """
    case = expand_case(TEMPLATE, "t")[0]
    bad = FakeLLM(dict(PARSE, differentials=[{"dx": "not_in_vocab", "weight": 1.0}]))
    out1, ran1 = run_case_arm("A", case, bad, tmp_path, index_db)
    assert ran1 and out1.error

    good = _llm()
    out2, ran2 = run_case_arm("A", case, good, tmp_path, index_db)
    assert ran2, "a stored failure must be retried, not loaded as done"
    assert out2.error is None and out2.items

    out3, ran3 = run_case_arm("A", case, good, tmp_path, index_db)
    assert not ran3 and out3.to_dict() == out2.to_dict()


def test_persist_and_resume(index_db, tmp_path):
    case = expand_case(TEMPLATE, "t")[0]
    llm = _llm()
    out1, ran1 = run_case_arm("A", case, llm, tmp_path, index_db)
    assert ran1 and (tmp_path / "A" / "syncope_003.json").exists()
    n_calls = len(llm.calls)
    out2, ran2 = run_case_arm("A", case, llm, tmp_path, index_db)
    assert not ran2 and len(llm.calls) == n_calls and out2.to_dict() == out1.to_dict()
    run_case_arm("C", case, llm, tmp_path, index_db)
    loaded = load_outputs(tmp_path)
    assert set(loaded) == {"A", "C"} and loaded["A"]["syncope_003"].record_ids == out1.record_ids
    m = json.loads(write_manifest(tmp_path, "fake-model", [case], {"arms": "A,C"}).read_text())
    assert m["model"] == "fake-model" and m["counts"] == {"A": {"outputs": 1, "errors": 0}, "C": {"outputs": 1, "errors": 0}}
    assert m["cases"]["inputs"] == 1 and "started_at" in m and m["unfrozen_cases"] == ["syncope_003"]
