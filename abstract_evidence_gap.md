# Where the evidence isn't: a pre-registered audit of diagnostic-accuracy coverage for bedside history and physical examination

**Status:** DRAFT — not signed off. Numbers traced in the appendix below.

---

**Background.** Bedside diagnosis rests on history and physical examination, and clinicians are
taught to weight findings by their diagnostic accuracy. How much of what a competent clinician
actually does at the bedside is backed by quantitative accuracy data has not been mapped against
independently specified clinical need.

**Methods.** We curated bedside discriminators — history questions, examination maneuvers,
functional tests and point-of-care ultrasound — across 12 inpatient presentations. Candidates
(n=153) were selected with deliberate enrichment for well-studied items: 78 (51.0%) were
classified a priori as likely supported by the JAMA Rational Clinical Examination series, only 27
(17.6%) as likely to lack quantitative data. Each underwent two independent AI-assisted
extractions (306 packets) against a schema requiring, for every estimate, a primary citation, a
verbatim quote and an exact table or page location. A physician verified every record against
source before promotion. Separately and beforehand, 36 cases spanning the 12 presentations were
authored blind, each with free-text targets stating what a competent clinician should ask or
examine. Cases and targets were hash-frozen before the library was queried, then mapped to
records.

**Results.** 153 records were verified from 306 extractions, citing 313 unique sources; all 337
retained estimates carried a verbatim quote and a source location. Only 83 records (54.2%) were
fully quantified, 33 (21.6%) partially, and 37 (24.2%) had no defensible quantitative data
despite relevant literature being identified — exceeding the 17.6% anticipated. Absence was
uneven by modality: 17 of 41 history items (41.5%) were unquantified versus 17 of 81 examination
maneuvers (21.0%). Of 258 blind-authored targets, 216 (83.7%) mapped to at least one record and
42 (16.3%) to none. Among 101 must-have targets, 9 (8.9%) had no record; 6 of those 9 were
history rather than examination, including establishing time last known well and obtaining
collateral history from nursing staff and family.

**Discussion.** In a sample chosen to favour well-studied findings, a quarter of curated bedside
discriminators had no usable accuracy data, and history was roughly twice as likely as
examination to lack it. Specifying clinical need before querying the library showed the residual
gap falls hardest on collateral history and chart review — actions clinicians treat as mandatory
but which accuracy methodology cannot describe, having no index test to characterise. These are
candidate priorities for primary study and a known blind spot for any evidence-linked bedside
tool. Limitations: a single physician verifier; synthetic rather than consecutive real cases;
targets authored by one clinician; AI-assisted extraction, human-verified but not independently
re-extracted.

---

## Traceability

Every number above, and where it comes from. Regenerate with the commands in `RUNLOG.md`.

| Claim | Value | Source |
|---|---|---|
| Presentations | 12 | `vocab.json` → `presentations` |
| Verified records | 153 | `records/verified/*.json` |
| Extraction packets | 306 (2 × 153 ids) | `records/extracted/*.json` |
| A priori `rce_backed` | 78/153 = 51.0% | `discriminator_ids.json` → `expected_evidence` |
| A priori `likely_not_quantified` | 27/153 = 17.6% | `discriminator_ids.json` → `expected_evidence` |
| Unique sources | 313 | `records/verified/*.json` → `sources[]`, deduped by DOI/PMID/citation |
| Estimates retained | 337, all with quote + location | `records/verified/*.json` → `estimates[]` |
| Fully quantified | 83/153 = 54.2% | `evidence_status == "quantified"` |
| Partially quantified | 33/153 = 21.6% | `evidence_status == "partially_quantified"` |
| Not quantified | 37/153 = 24.2% | `evidence_status == "not_quantified"`; all 37 have `estimates == []` |
| History unquantified | 17/41 = 41.5% | `identity.type == "history"` ∩ `not_quantified` |
| Exam unquantified | 17/81 = 21.0% | `identity.type == "exam"` ∩ `not_quantified` |
| Base cases | 36 | `benchmark/cases/*.json` |
| Freeze commit | `39a698e` | `frozen_commit` field, identical in all 36 cases; guarded by `tests/test_freeze.py` |
| Targets total | 258 | `benchmark/target_map.json` → `_counts.targets` |
| Targets mapped | 216 = 83.7% | `_counts.mapped` |
| Targets unmapped | 42 = 16.3% | `_counts.unmapped` |
| Must-have targets | 101 | `_counts.must_have_targets` |
| Must-have unmapped | 9 = 8.9% | `_counts.must_have_unmapped` |
| Of those, history-type | 6 of 9 | `_unmapped` where `must_have`, classified by hand — see below |

The 9 must-have targets with no record, classified:

| # | Case | Target (abbreviated) | Kind |
|---|---|---|---|
| 1 | `aki_003` | Compartment exam: tense tender swelling, pain on passive stretch | exam |
| 2 | `fever_001` | Inspect surgical wound for erythema, drainage, dehiscence | exam |
| 3 | `palpitations_002` | Cannon a waves, variable S1 (AV dissociation) | exam |
| 4 | `ams_003` | Ask nurse and family: baseline cognition, what changed, when | **collateral history** |
| 5 | `weakness_001` | Establish last-known-well time precisely | **collateral history** |
| 6 | `dyspnea_002` | Known COPD diagnosis, prior spirometry, inhalers, prior intubation | **chart review** |
| 7 | `chest_pain_002` | Onset abrupt at rest vs after cough/strain; prior pneumothorax | patient history |
| 8 | `palpitations_002` | Prior similar episodes since youth; stopped with breath-holding | patient history |
| 9 | `weakness_003` | Focal vs generalized, sudden vs gradual, new vs progressive | patient history |

Rows 4–6 are the structural claim in the Discussion: collateral history and chart review have no
index test to characterise, so no accuracy study can produce an estimate for them. Rows 7–9 are
ordinary patient history and *could* in principle be studied — the Discussion does not claim
otherwise.

## Word count

Body (Background through Discussion): 409 words. Trim targets if a venue caps at 300: the
methods detail on extraction schema, and the final limitation clause.
