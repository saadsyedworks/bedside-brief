from __future__ import annotations

import json

from eval.cases import expand_case
from eval.mapping import attach, components, jaccard, library_coverage, load_target_map, phrase_matches, propose_mapping, target_text_matches, tokens
from tests.test_eval_cases import TEMPLATE


def test_tokens_fold_aliases_stopwords_and_plurals():
    assert tokens("Jugular venous pressure elevated") == {"jvp", "elevat"}
    assert tokens("Ask about the signs") == set()  # all stop words
    assert tokens("crackles") == tokens("crackle")


def test_target_text_matching_rules():
    assert target_text_matches("JVP", "Assess the JVP at 45 degrees")
    assert target_text_matches("S3 gallop", "Listen for an S3")
    assert target_text_matches("Orthostatic vital signs (supine to standing at 1 and 3 min)",
                               "Orthostatic vitals: SBP drop >=20 / DBP >=10 mmHg or pulse increment >=30/min at 1-3 min standing")
    assert target_text_matches("Peritoneal signs (rigidity, percussion tenderness, rebound, cough test)", "Check for rebound tenderness and guarding")
    assert not target_text_matches("Ask about dysuria or hematuria", "Ask about fever")
    assert not target_text_matches("Ask: prior biliary colic, known gallstones, and alcohol use", "Ask about fever and chills")
    assert components("Psoas sign and obturator sign") == ["Psoas sign", "obturator sign"]
    assert phrase_matches("Late-peaking systolic murmur", "harsh late-peaking murmur radiating to carotids")
    assert jaccard([], []) == 1.0 and jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_propose_mapping_writes_proposed_file_and_attach_coverage(tmp_path):
    cases = expand_case(TEMPLATE, "t")
    entries = [{"id": "exam_late_peaking_murmur", "title": "Late-peaking systolic murmur with soft S2 and slow carotid upstroke"},
               {"id": "fn_orthostatic_vitals", "title": "Orthostatic vital signs"},
               {"id": "hx_syncope_prodrome", "title": "Prodrome before loss of consciousness (nausea, warmth, palpitations)"}]
    out = tmp_path / "proposed.json"
    prop = propose_mapping(cases, out_path=out, entries=entries)
    assert out.exists() and prop["_status"].startswith("PROPOSED")
    m = {e["target_index"]: e["record_ids"] for e in prop["syncope_003"]}
    assert m[0] == ["exam_late_peaking_murmur"] and m[2] == ["fn_orthostatic_vitals"] and "hx_syncope_prodrome" in m[1]
    tm = load_target_map(out)
    attach(cases, tm)
    assert cases[1].targets[2].mapped_ids == ["fn_orthostatic_vitals"]  # variants inherit the base mapping
    cov = library_coverage(cases, {"fn_orthostatic_vitals", "exam_late_peaking_murmur"})
    assert (cov["targets"], cov["mapped_to_verified"]) == (3, 2) and abs(cov["coverage"] - 2 / 3) < 1e-9
    assert cov["uncovered"][0]["target_index"] == 1
    assert load_target_map(tmp_path / "missing.json") == {}
    assert json.loads(out.read_text())["syncope_003"][0]["scores"]
