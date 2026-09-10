# Case critique — RE-CHECK after author revisions (single pass)

Reviewer: case-critic subagent, 2026-09-10. Scope: all 36 base cases (108 inputs) in `benchmark/cases/`, revised commit `09cc20b` vs pre-critic `3d65e36`. Inputs: `agents/case_critic.md`, `benchmark_case_template.json`, `vocab.json`, `critique_part1.md`, `critique_part2.md`, DECISIONS #11–#15. Not read: `records/`, `discriminator_ids.json`, scratchpad. No web.

Method: (a) field-level diff of every case between the two commits to confirm each first-pass "revise" item was applied or explicitly rejected; (b) scripted mechanical pass over all 36 files (off-bedside terms inside `reference_targets_freetext[].item`, word-level diff base→p1, noise `expected_change` prefix, `_p1`/`_n1` ids, filename = case_id, differentials ∈ vocab, target and must_have counts, ≤1 POCUS non-must); (c) canonical-phrase scan against DECISIONS #15; (d) `python3 tools/validate.py cases` → **0 errors, 0 warnings**.

**Verdicts: 26 pass / 10 fix.** Of the 10 fixes, 2 are blocking [B] (an off-bedside term inside a must_have; a must_have that the perturbation says "becomes must-have"), 8 are wording-level [W] (canonical strings; `expected_change` sentences that claim an already-must_have item "becomes must-have", which makes that transition unmeasurable — the same defect the first pass flagged on syncope_003).

## 1. Per-case table

| case_id | verdict | residual issue (exact text to change, if any) |
|---|---|---|
| dyspnea_001 | pass | All three first-pass items applied (single-addition fever p1; should_not #2 replaced; t6 trimmed). |
| dyspnea_002 | fix [W] | Flags swapped as requested (COPD history must_have; Anthonisen and work-of-breathing demoted → 2 must_have). Label/one-liner mismatch: `perturbation_pair.changed_feature` says "pleuritic" but the p1 one-liner says only "sudden right-sided chest pain". Change `perturbation_pair.changed_feature`: `"presenting symptom: wheeze -> sudden right-sided pleuritic chest pain"` → `"presenting symptom: wheeze -> sudden right-sided chest pain"`. |
| dyspnea_003 | pass | "whether the pain is pleuritic" replaced with "syncope or presyncope with the event". |
| chest_pain_001 | pass | t2 split (BP both arms / pulse deficit vs tearing-pain question); AR kept as parenthetical (rejection accepted, §6). |
| chest_pain_002 | pass | p1 replaced with the critic's exact wording; one feature (pain quality/position). Not re-branched (rejection accepted, §6). |
| chest_pain_003 | pass | should_not #2 now case-specific (AKI/NSAID); Hamman crunch / subcutaneous emphysema added to t5. `esophageal_gerd` not added (rejection accepted, §6). |
| dizziness_001 | pass | p1 replaced with the critic's wording (gait statement removed as instructed — entailed by the trigger swap, since gait failure contradicts BPPV); `medication_effect` → `anemia`. |
| dizziness_002 | pass | MAR phrasing canonical. |
| dizziness_003 | pass | Orthostatics demoted to must_have:false with rationale; both must_haves are disambiguating questions. |
| syncope_001 | pass | — |
| syncope_002 | pass | MAR must_have retained (not_quantified, flagged §5). |
| syncope_003 | fix [B] | Swap applied (witness account demoted, volume status promoted). But the promoted must_have t3 contains the I/O chart term "urine output" (DECISIONS #11: I/Os = off-bedside monitoring) and two non-canonical strings. Change `reference_targets_freetext[2].item`: `"Assess volume status: oral intake, vomiting, urine output, dry axillae and mucous membranes, capillary refill"` → `"Assess volume status: ask about oral intake, vomiting, and whether he has been passing urine; Dry axilla / mucous membranes; Capillary refill time"`. |
| palpitations_001 | pass | Neck-pounding item added (non-must, rises in p1); triggers demoted; JVP/crackles promoted (Wang 2005). |
| palpitations_002 | pass | Admission context added; neck-pounding added; hemodynamic-stability must_have retained (rejection accepted, §6). |
| palpitations_003 | fix [W] | Stimulant question demoted; pallor/orthostatics promoted. `expected_change` says the Orthostatic vital signs item "rise[s] to must_have" but it is already must_have in base (t5). Change `perturbation_pair.expected_change` → `"Sinus tachycardia secondary to infection now dominates: Capillary refill time and examination of the cellulitis margin for progression or abscess rise to must_have; the Conjunctival pallor/Orthostatic vital signs item remains must_have; thyroid examination drops to should-still-include; the medication/stimulant question remains."` |
| edema_001 | pass | p1 single addition; should_not #1 replaced with venous-duplex item. |
| edema_002 | pass | — |
| edema_003 | pass | `venous_insufficiency` dropped (3 differentials; `cellulitis_ssti` and `pulmonary_embolism` are cross-presentation vocab terms, validator-legal — they were already present pre-critic). PE screen demoted → 2 must_have. |
| hypotension_001 | pass | SpO2 removed from t6; noise "confused, which is new for him"; fluid balance/UOP moved to off_bedside; source exam must_have retained (rejection accepted, §6). Cosmetic only: t6 "examine calves for Calf circumference asymmetry >3 cm" reads awkwardly but carries the canonical string. |
| hypotension_002 | pass | t2 demoted with conditional wording; should_not reworded; p1 = critic's wording (one mechanism swap); `atrial_fibrillation_flutter` retained (rejection accepted, §6). Optional cosmetic: t2 has a double parenthetical — `"Orthostatic vital signs (supine to standing at 1 and 3 min) (postural pulse increment >=30/min), only if supine SBP >=90"` → `"Orthostatic vital signs (supine to standing at 1 and 3 min), postural pulse increment >=30/min, only if supine SBP >=90"`. |
| hypotension_003 | pass | Rationale of t1 now conditional ("When effusion is suspected"). Optional: t4 "pericardial rub" is a residual variant of the canonical rub string (non-must, inside a compound) — see §3. |
| ams_001 | pass | SpO2 restored in p1; t6 trimmed (glasses/hearing aids moved to off_bedside as a treatment-category item); MAR must_have retained (rejection accepted, §6). |
| ams_002 | pass | should_not #1–2 replaced; t2 split into "Abdominal tenderness (SBP)" + melena/DRE item; ammonia parenthetical dropped. `sbp` is cross-presentation vocab (validator-legal). |
| ams_003 | pass | SpO2 removed from t5 (pulse oximetry now in off_bedside). |
| abdominal_pain_001 | pass | p1 single feature (RLQ→LLQ, age kept); psoas/obturator demoted; t1 replaced by "RLQ tenderness (McBurney point)"; vomiting-order question non-must; CT boilerplate removed. 2 must_have. |
| abdominal_pain_002 | fix [W] | `expected_change` says "mental status and blood pressure check … becomes must-have" but mental status is already inside must_have t2 (and scleral icterus is answered by the p1 one-liner). Change `perturbation_pair.expected_change` → `"Cholangitis moves to the top; the jaundice/mental status item remains must_have and a blood pressure check for Reynolds pentad is a new item; Murphy sign drops to should-still-include; ask about prior biliary stents, ERCP, or known stones becomes must_have."` Should_not swap not applied (suggestion-only; accepted, §6). |
| abdominal_pain_003 | fix [W] | Noise "severe" restored; should_not #3 replaced; "both arms" removed from p1. Residual: `expected_change` says pulsatile mass / femoral pulses "become must-have" but t3 is already must_have. Change `perturbation_pair.expected_change` → `"AAA rupture becomes the leading differential; pulsatile mass palpation and bilateral femoral pulses remain must-have and lead the card; the back or flank pain question becomes must-have; pain-out-of-proportion assessment drops to should-still-include; rectal exam for blood drops."` |
| fever_001 | fix [W] | "oxygen saturation" removed; t3 reworded (no turbidity); should_not #2 replaced; scaffold varied to knee arthroplasty. Residuals: (a) t1 is a non-canonical consolidation/crackles string — change `reference_targets_freetext[0].item`: `"Respiratory rate; focal crackles, egophony, dullness, and bronchial breath sounds on lung auscultation"` → `"Respiratory rate; Focal consolidation: egophony, bronchial breath sounds, dullness to percussion; Focal crackles"`. (b) `expected_change` says wound inspection "become[s] must-have" but t2 already is — change `perturbation_pair.expected_change` → `"Intra-abdominal abscess or anastomotic leak enters the top differential; abdominal exam for distension and peritoneal signs becomes must-have; wound inspection remains must-have; lung exam stays but drops to should-still-include; ask about flatus, bowel function, and drain output rises."` |
| fever_002 | pass | t3 demoted and reworded (no re-examine-in-1–2 h clause). "becomes the top must-have" in p1 refers to rank of an existing must_have — acceptable. |
| fever_003 | fix [B] | Untouched since first pass. Two problems on one item: t3 "Ask about stool frequency and consistency; examine the abdomen for distension and tenderness" is must_have in base, yet p1 `expected_change` says "abdominal exam … becomes must-have" (unmeasurable transition — same defect the first pass flagged on syncope_003); and it makes fever_003 the only case with 3/3 guideline-only must_haves (DECISIONS #14 asks for indispensability — stool history in a patient the RN reports as "no localizing sx" is a should-include, not indispensable). Change `reference_targets_freetext[2].must_have`: `true` → `false` (must_have count becomes 2; validator minimum is 2). Should_not swap not applied (suggestion-only; accepted, §6). |
| weakness_001 | pass | changed_feature label corrected ("added: …"). |
| weakness_002 | pass | Case-only variants ("digital rectal examination (DRE)", "bladder percussion/palpation") — see §3. |
| weakness_003 | fix [W] | PT wording applied. Residual: `expected_change` says "pronator drift confirmation, facial symmetry … become must-have" but t2 (Pronator drift, facial symmetry) is already must_have. Change `perturbation_pair.expected_change` → `"Underspecified flag should clear; stroke becomes the leading differential; Pronator drift and facial symmetry remain must-have; language testing and last-known-well time become must-have; proximal strength testing and refeeding/diuretic questions drop to should-still-include."` |
| aki_001 | fix [W] | Weights/net balance moved to off_bedside; JVP and Abdominojugular reflux split. Residual canonical variant: change `reference_targets_freetext[3].item`: `"Lung crackles, S3 gallop, and peripheral edema"` → `"Bibasilar crackles, S3 gallop, and peripheral edema"`. |
| aki_002 | fix [W] | Volume bundle split; canonical strings. Residual: `expected_change` says "volume exam and medication history become the top must-haves" but both (t2 MAR, t3 orthostatics) are already must_have. Change `perturbation_pair.expected_change` → `"NSAID-related prerenal AKI, ATN, and AIN rise; Orthostatic vital signs and Medication review (MAR) remain must-have and lead; the JVP and dry axilla / mucous membranes item rises; Bladder percussion/palpation for retention remains must-have as a reversible cause; ask about new rash, fever timing, and arthralgia for AIN becomes must-have; anticholinergic question drops."` Optional case-only variant in t6 ("costovertebral angle (CVA) tenderness") — see §3. |
| aki_003 | pass | p1 = critic's NSAID wording with the dark-urine red herring declared; t5 reworded; skin turgor dropped. "ask about urine volume since admission" is a history question put to patient/nurse (DECISIONS #11 puts I/O *chart review* off-bedside), and it is the wording the first pass prescribed — accepted. |

### First-pass items neither applied nor justified
None. Every "revise" line in `critique_part1.md` and `critique_part2.md` was either applied (verified by field diff against `3d65e36`) or is one of the seven stated rejections ruled on in §6. Cross-case requests were handled by DECISIONS #11 (bedside boundary), #13 (compound targets), #15 (canonical strings); the reused noise-variant details were varied but the duplication was partly *moved* rather than removed (see §2, non-blocking).

## 2. Mechanical checks (all 36)

- **Off-bedside terms inside target items**: one true hit — syncope_003 t3 "urine output" (must_have) → FIX above. aki_003 t5 "ask about urine volume since admission" accepted as history (see table). palpitations_003 t4 "weight loss" is a symptom, not a weights chart (false positive). No SpO2 / pulse ox / telemetry / glucose / bladder scan / lab / imaging / ECG term remains in any item. POCUS: exactly ≤1 per case, all `must_have: false` (chest_pain_002, hypotension_003, abdominal_pain_002, aki_001).
- **Perturbation = one clinical feature (word diff)**: 36/36 pass. Single-token swaps/additions in 27; the 9 multi-token diffs are each one clinical feature: dizziness_001 (trigger swap + removal of the gait statement it contradicts — prescribed by first pass), hypotension_002 (anticoagulant → loop diuretic, AF kept), weakness_002 (comorbidity swap necessarily changes admission reason — accepted first pass), edema_002 (risk-factor swap), edema_003 (laterality; "pain" → "aching" accepted first pass), aki_003 (found-down → NSAID exposure, first-pass wording), ams_003 ("no further details" replaced by the admitting diagnosis), fever_003 (rigors → watery stools), chest_pain_002 (pain quality/position, first-pass wording).
- **Noise variants**: none adds clinical meaning; all 36 `expected_change` start with "None."; "confused, which is new for him" (hypotension_001) and "severe" (abdominal_pain_003) corrected. Borderline but accepted: syncope_003_n1 "roommate heard him fall" (base already implies an observer of pallor). Occupation tokens are now duplicated in new places (bus driver ×3, librarian ×3, machinist ×2, line cook ×2, trucker ×3, electrician ×2, accountant ×2, teacher ×3) — harmless because the parser emits vocab only, so noise tokens cannot become retrieval keys; no edit required.
- **case_id naming**: 36/36 filename = case_id = `<presentation>_<nnn>`, `_p1`/`_n1` suffixes correct.
- **Differentials**: 36/36 vocab strings; counts 3–4. Cross-presentation (validator checks the vocab union; DAY1 freeze expects cross-presentation retrieval): ams_002 `sbp`; hypotension_002 `atrial_fibrillation_flutter`; edema_003 `cellulitis_ssti`, `pulmonary_embolism`.
- **Targets per case**: 5–6; **must_have per case**: 2 or 3 in all 36 (total 102; 100 after the fever_003 demotion… see §5).

## 3. Canonical phrasing (DECISIONS #15) — residual variants

| maneuver | status | residual variants |
|---|---|---|
| Orthostatic vital signs (supine to standing at 1 and 3 min) | consistent (12 items) | hypotension_002 t2 double parenthetical (cosmetic, optional edit in table) |
| JVP (verbatim) | consistent (13 items) | none; palpitations_002 "Cannon a waves in the jugular venous pulse" is a separate maneuver by design |
| Abdominojugular reflux | consistent (3) | none; no "hepatojugular" left |
| Calf circumference asymmetry >3 cm | consistent (9) | none |
| Medication review (MAR): … | consistent (16) | none |
| Bladder percussion/palpation for retention | consistent (6) | weakness_002 t3 lowercase "bladder percussion/palpation for retention" (case only) |
| Pronator drift | consistent (5) | none |
| HINTS exam (head impulse, nystagmus, test of skew) | consistent (1) | none |
| Dix-Hallpike maneuver | consistent (1 + supine-roll reference) | none |
| Murphy sign | consistent (1 + "sonographic Murphy sign" in POCUS item) | none |
| CAM delirium screen (attention: months backward) | consistent (2) | none |
| Bibasilar crackles / Focal crackles | 11 of 13 | **aki_001 t4 "Lung crackles"** (FIX); **fever_001 t1 "focal crackles" inside a non-canonical consolidation string** (FIX) |
| Pulsus paradoxus | consistent (2) | none |
| S3 gallop | consistent (5) | none |
| Neck stiffness, Kernig, Brudzinski, jolt accentuation | not used (no meningitis case) | — |
| Secondary strings from the critics' tables (not in #15): Capillary refill time | 4 of 5 | **syncope_003 t3 "capillary refill"** (covered by FIX) |
| Dry axilla / mucous membranes | 2 of 3 (+ hypotension_002_p1) | **syncope_003 t3 "dry axillae and mucous membranes"** (covered by FIX) |
| Pericardial friction rub (leaning forward, end-expiration) | 2 of 3 | hypotension_003 t4 "pericardial rub" (non-must, compound) — optional: `"Heart sounds (muffled), Pericardial friction rub (leaning forward, end-expiration), and lung auscultation for Bibasilar crackles versus clear fields"` |
| Costovertebral angle (CVA) tenderness | 4 of 5 | aki_002 t6 lowercase "costovertebral angle (CVA) tenderness bilaterally" (case only) |
| Focal consolidation: egophony, bronchial breath sounds, dullness to percussion | 2 of 3 | fever_001 t1 (covered by FIX) |
| Gait assessment / Witness account / Peritoneal signs / Compare breath sounds side to side; percuss for unilateral hyperresonance / Digital rectal examination (DRE) | consistent | weakness_002 t3 lowercase "digital rectal examination (DRE)" (case only) |

Case-only variants need no edit if the Phase-3 matcher is case-insensitive; if it is exact-string, capitalize the three noted items.

## 4. Underspecified cases

Count = **3**, as expected: `dizziness_003`, `ams_003`, `weakness_003`; all other 33 are `false` and correctly so.
- dizziness_003: both must_haves are disambiguating questions (timing; triggers/quality); orthostatics demoted to should-include with the ask-first rationale.
- ams_003: must_have #1 is the disambiguating question (baseline, what changed, LKW); #2 CAM and #3 focal screen are the two bedside screens that resolve the branch point (delirium vs focal deficit) when the patient cannot answer. Confirmed.
- weakness_003: must_have #1 is the disambiguating question (focal vs generalized, onset); #2 Pronator drift/facial symmetry and #3 proximal strength resolve the same branch point when PT's report cannot. Confirmed.
Note for the coordinator: dizziness_003 demoted a maneuver (orthostatics) under the ask-first rule while ams_003/weakness_003 keep two maneuvers each. This is consistent under one stated rule — *in an underspecified case, must_have = whatever resolves the branch point, question or screen; a maneuver that tests only one branch (orthostatics presumes a standing trigger) is not must_have.* No edit proposed; record the rule if the eval "ask-first" metric will be computed on must_have questions only.

## 5. must_have counts and guideline-only (not_quantified) must_haves — DECISIONS #14

must_have per case: 3 in 30 cases; 2 in abdominal_pain_001, dizziness_002, dizziness_003, dyspnea_002, edema_003, fever_002 (and fever_003 after the fix). Total 102 → 101 after the fever_003 demotion.

Items expected to map ONLY to guideline-tier / `not_quantified` records (no RCE or diagnostic-accuracy anchor for the maneuver itself), with verdict:

| case | must_have item (short) | verdict |
|---|---|---|
| palpitations_002 #1 | Bedside hemodynamic stability (mentation, chest pain, dyspnea, CRT, skin temp) | justified |
| syncope_002 #3 | Medication review (MAR): sotalol, QT/AV-nodal agents | justified |
| hypotension_001 #2 | Source examination (compound; the Focal crackles component may map to a quantified pneumonia record) | justified |
| ams_001 #2 | Medication review (MAR): opioids, benzodiazepines, anticholinergics; pain | justified |
| ams_001 #3 | Infection source examination (compound; Focal crackles / CVA components partially quantified) | justified |
| ams_002 #1 | Asterixis and West Haven grading | justified |
| ams_002 #2 | Abdominal tenderness (SBP) | justified |
| ams_003 #1 | Ask baseline cognition, what changed, LKW | justified |
| dizziness_001 #3 | Confirm timing and triggers (TiTrATE) | justified |
| dizziness_002 #2 | Ask episode duration, trigger, symptom-free interval | justified |
| dizziness_003 #1, #2 | Ask timing; ask triggers/quality | justified |
| chest_pain_003 #2 | Ask positional relief / worse supine; recent viral illness | justified |
| abdominal_pain_002 #2 | Scleral icterus / jaundice plus mental status (Tokyo / Reynolds) | justified |
| abdominal_pain_002 #3 | Ask radiation to back, prior colic, alcohol, gallstones | justified (borderline — no quantified alternative exists) |
| abdominal_pain_003 #1 | Pain out of proportion to exam | justified |
| aki_002 #1 | Bladder percussion/palpation for retention | justified |
| aki_002 #2 | Medication review (MAR) + void history | justified |
| aki_003 #1 | Compartment exam | justified |
| aki_003 #3 | Ask down time, seizure, substances, muscle pain | justified |
| fever_001 #2 | Surgical wound inspection | justified |
| fever_002 #2 | Joint exam, pain with passive ROM (Margaretten quantifies risk factors, not the exam) | justified |
| fever_003 #1 | PICC site / tract inspection | justified |
| fever_003 #2 | New/changed murmur + peripheral stigmata | justified |
| fever_003 #3 | Stool frequency/consistency + abdominal exam | **demote** (FIX applied above; 3/3 not_quantified in one case fails the "indispensable" test and the p1 logic) |
| weakness_001 #1 | Forehead sparing | justified |
| weakness_001 #3 | Last-known-well time and apixaban last dose | justified |
| weakness_002 #1, #2, #3 | Sensory level; reflexes/Babinski/tone; saddle/anal tone/bladder | justified (×3) |
| weakness_003 #1 | Ask focal vs generalized, onset | justified |
| weakness_003 #3 | Proximal strength (sit-to-stand, hip flexion, arms overhead) | justified |

Count: 32 must_have items in this list (31 after the fever_003 demotion) ≈ 31% of must_haves — higher than the "12" cited in `tools/gate_package.py` and in line with the part-2 critic's ~40% estimate; the gate note should be updated to this list. Items with partial or modest quantification that I did NOT list (a record with numbers can be written): fever_001 #3 (CVA tenderness, Bent 2002), hypotension_001 #1/#3 and hypotension_003 #3 (CRT/mottling, qSOFA — prognostic numbers), palpitations_001 #2 and palpitations_003 #1 (Thavendiranathan 2009, modest LRs), chest_pain_003 #1 (rub: published sens/spec), dyspnea_003 #3 and chest_pain_002 #3 (hyperresonance LRs), syncope_003 #3 (dry axilla, McGee 1999).

## 6. Rulings on the authors' stated rejections

1. **chest_pain_002 not re-branched toward pneumothorax — accept.** Within-presentation coverage (ACS / PE / pericarditis) meets the brief; the VTE-triplication note was explicitly "not a rule violation", and re-branching now would re-author targets after the critic pass.
2. **chest_pain_003 `esophageal_gerd` not added — accept.** The differential is at the 4-item cap, `esophageal_gerd` denotes reflux and is a poor proxy for post-emetic esophageal injury, and the new Hamman-crunch / subcutaneous-emphysema item captures the clinical point.
3. **chest_pain_001 AR murmur kept as parenthetical — accept.** Under DECISIONS #13 the compound maps to a set and is present if any id is on the card, and DECISIONS #8 keeps a dedicated dissection-AR id, so the parenthetical adds a mapping route without inflating must_have recall (the item's primary anchors remain pulse deficit / inter-arm BP, Klompas 2002).
4. **palpitations_002 #1 hemodynamic stability kept must_have — accept under DECISIONS #14.** ACLS-standard and indispensable at HR 170 / BP 104/68; no literature-backed substitute exists for the stable-vs-unstable gate. Listed as not_quantified in §5.
5. **hypotension_001 #2 source exam and ams_001 #2 MAR review kept must_have — accept under DECISIONS #14.** Both rationales now state the "indispensable, no literature-backed substitute" clause; hypotension_001 #2 also carries a quantified component (Focal crackles). Listed in §5.
6. **hypotension_002 `atrial_fibrillation_flutter` retained — accept.** `tools/validate.py` checks the vocab union, and DAY1 freeze expects cross-presentation retrieval; the first-pass request ("confirm the parser can emit it under hypotension") is an eval-harness check, not a case defect.
7. **abdominal_pain_002 and fever_003 should_not swaps not applied — accept.** Both were labelled suggestion-only, and the existing items (HIDA/CT before Murphy and jaundice assessment; echocardiogram before auscultation and line-site inspection) remain genuinely inappropriate sequencing errors. fever_003 is still marked fix, but on the separate t3 must_have / p1-logic ground above.
