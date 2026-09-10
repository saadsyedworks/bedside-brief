"""Emit the extractor subagent prompt for a batch of ids and one agent letter (A or B).

  python tools/extract_prompt.py A exam_jvp_elevated exam_s3_gallop ...   > /tmp/prompt.txt
A and B get the same procedure but different search phrasing and ordering so runs are independent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.record_skeleton import skeleton  # noqa: E402

STYLE = {
    "A": "Search order: (1) `python3 tools/pubmed.py search '<finding> Rational Clinical Examination[Title]'`, (2) `'<finding> sensitivity specificity meta-analysis'`, (3) `'<finding> likelihood ratio prospective'`. Prefer pooled estimates; add a primary-study estimate only when the pooled one is absent or population-split.",
    "B": "Search order: (1) `python3 tools/pubmed.py search '<finding> diagnostic accuracy systematic review'`, (2) `'<finding> likelihood ratio'`, (3) `'Does this patient have <condition>[Title]'` (JAMA RCE). Prefer the largest prospective cohort or the RCE pooled table; add a second estimate when setting (ED vs inpatient) changes performance.",
}


def build(agent: str, ids: list[str]) -> str:
    sks = {i: skeleton(i, agent) for i in ids}
    return f"""You are **extractor-{agent}**, one of two INDEPENDENT extraction agents for Bedside Brief (repo /home/user/bedside-brief). Read first: agents/extractor.md, extraction_packet_spec.md, discriminator_schema.json, vocab.json. Never open records/extracted/ (the other extractor's packets live there) and never read records/redteam/.

Network: use ONLY Bash with `python3 tools/pubmed.py <search|fetch|pmc|fulltext|doi|grep> ...` (NCBI e-utils + Crossref; PubMed abstracts and PMC open-access full text are reachable; `fulltext <PMID>` returns PMC body text when it exists, up to 200 kB — pipe through `grep -n` for table rows). WebSearch works for discovery; WebFetch is blocked. Publisher sites are blocked, so `location` must come from the abstract ("Abstract, Results") or PMC full text ("Table 2", "p. 1234") — if you cannot see the table/page yourself, the estimate is NULL and you explain in extraction_notes. Never fabricate a PMID/DOI: confirm every one with `tools/pubmed.py fetch <pmid>` or `doi <doi>` and check the title matches.

{STYLE[agent]}

For EACH id below, fill the provided skeleton and write it to `records/extracted/{{id}}__extractor-{agent}.json`. Rules (hard):
- Keep identity and clinical_mapping as seeded (you may ADD differentials/indication_tags from vocab.json only). Delete the two `_anchor_source`/`_expected_evidence` helper keys before saving.
- Every numeric estimate needs: sources[] entry with pmid or doi (confirmed), a verbatim quote ≤25 words that contains the number, and location. Set `computed=true` + `computed_from` if you derive LR from a 2×2 or sens/spec. Never derive sens/spec from an LR.
- Separate `estimates[]` entries per population/setting/threshold when performance differs; never average.
- evidence_status: quantified (≥1 numeric estimate with quote+location) / partially_quantified (some estimate fields null or only one direction reported) / not_quantified (estimates=[] and sources[] cites the guideline/consensus).
- UNITS: sensitivity/specificity/prevalence values are PROPORTIONS 0–1 (write 0.82, not 82); LRs are ratios. Quotes keep the source's wording.
- DIRECTION: `lr_positive` = likelihood ratio when the finding is PRESENT; `lr_negative` = when ABSENT. If the source reports the inverted sign (e.g. "absence of tenderness LR 0.23"), relabel explicitly, set computed=true and explain in computed_from.
- RANGES: never enter a between-study range (e.g. "LR 8.0–101") as a point value. Leave the field null and put the range in extraction_notes; only pooled point estimates go in `value`.
- COMPOSITES: if the source's finding is a composite (e.g. "JVD at rest OR inducible", "pulse deficit OR BP differential", "orthopnea OR PND"), you may enter it only with target_condition prefixed "COMPOSITE: …" and a note; never present a composite as this single sign's own estimate.
- ONE NUMBER MINIMUM: an `estimates[]` entry must carry at least one numeric field; otherwise delete it and describe the gap in extraction_notes. `prevalence` only from cohort designs (never case-control ratios).
- PROGNOSTIC vs DIAGNOSTIC: outcomes like mortality are not diagnostic accuracy; if you include them, target_condition must start "PROGNOSTIC: …".
- AUTHORS: copy `sources[].citation` author names from `tools/pubmed.py fetch` output (it returns `authors`); never from memory.
- NOTES DISCIPLINE: any number in extraction_notes/interobserver_note/pitfalls must also have a quote+location, or be tagged "(unverified recall)".
- STATUS RULE: quantified = every estimate has ≥1 numeric field AND ≥1 estimate has both a sens/spec pair or an LR pair; partially_quantified = some numeric fields present but the above not met; not_quantified = no numeric estimate at all.
- technique.how ≤400 chars; changes_what ≤200 chars; ≤2 sentences per prose field; POCUS records need safety_scope.skill_assumption.
- After writing all files run `python3 tools/validate.py records records/extracted` and fix until your files show 0 errors (ignore other agents' files in the output).
Reply with one line per id: id | evidence_status | n_estimates | primary PMID(s) | any problem.

Skeletons:
```json
{json.dumps(sks, indent=1)}
```"""


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2:]))
