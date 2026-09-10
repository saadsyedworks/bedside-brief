# Red-team review — wave 3 (37 ids, 74 packets)

Reviewer: red-team subagent, 2026-09-10. Scope: extends `records/diff_report.md` (mechanical) with judgment; wave-3 packets predate the wave-4 prompt hardening (DECISIONS #23), so this review also records whether the wave-1 weaknesses recurred.
Method: every packet read. For every estimate with a `source_index`, the quote (split at "…") was searched in the PubMed abstract and, where not found, in the PMC full text (`tools/pubmed.py fetch|grep|fulltext`): 108 quoted estimates across 74 packets, 107 found verbatim, 1 altered (see `hx_dysuria_frequency`). Every `sources[].pmid` (96 unique) was fetched and its first author compared with the citation string. Table-located quotes verified in PMC full text: Kattah 2009 Tables 1 and 4 (PMID 19762709), Akaishi 2019 Table 2 (31516806), Tarnutzer 2023 Results/Figure text (37038843), Dumas 2019 Results (31182133), Downie 2013 Results and Figure 4 legend (24335669).
Categories: NUMERIC MISMATCH · NO LOCATION · SECONDARY SOURCE · SILENT COMPUTATION · POPULATION COLLAPSE · VOCAB VIOLATION · SCOPE · FABRICATION SUSPECT · DIRECTION · UNITS · STATUS · AUTHOR MISMATCH · COMPOSITE.
"VERIFIED" lines record what resolved cleanly so the owner need not repeat the lookup.

Batch-wide results first:
- **UNITS**: no sensitivity/specificity/prevalence outside 0–1 in any packet; every percent quote matches its stored proportion. Four `lr_negative = 0.0` values (Kattah HINTS ×2, Attia jolt ×2) are printed in the sources but the validator (correctly) wants null + note: a literal 0 LR zeroes any Bayes update. Otherwise clean.
- **FABRICATION SUSPECT (numbers)**: none. Every number checked exists in its cited source at the stated location. **FABRICATION SUSPECT (citations)**: three distinct author-list errors in extractor-B, six packets affected (below). The PMIDs resolve to the right papers; the author strings were typed from memory.
- **AUTHOR MISMATCH**: B ×6 (above). Extractor-A has no wrong names but omits the author list entirely for PMIDs 36453134 (Shah VP et al., GRACE-3; 4 packets), 38990511 (Martinez C et al.; 1 packet) and 22956117 (O'Phelan KH et al.; 1 packet). Accent-only differences (Böhner, López-Escámez) ignored.
- **SILENT COMPUTATION**: all 16 diff-report `LR+ equals sens/(1-spec) but computed=false` hits are false positives — the LR is printed in the source (Summers 2010 abstract; Wong 2018 abstract; Herbst 2014 abstract; Halker 2008 abstract; Kattah 2009 Results; Akaishi 2019 Table 2; Attia 1999 abstract; Cooke 2006 abstract). No true silent computation. Three *disclosed* computations deserve scrutiny (`hx_back_pain_cancer_history` A, `exam_meningeal_signs…` B, `fn_hints_exam` B).
- **SECONDARY SOURCE**: no number rests on a textbook/UpToDate/narrative review. One borderline: `fn_dix_hallpike` (both) takes its headline numbers from a critically appraised topic (Halker 2008), whose single primary study is unnamed in the abstract; the primary (Cohen 2004) has no sens/spec in its abstract.
- **NO LOCATION**: every numeric estimate has a quote + location. Residual issues are five "empty" estimates (all numeric fields null, quote holds an RR/OR/range) and numbers recalled from unviewed JAMA tables in `extraction_notes` (Wagner 1996 ×5 packets).
- **VOCAB**: no term outside `vocab.json`. Soft cross-presentation differentials (term exists but not under any listed presentation): `cholangitis` (`hx_rigors_shaking_chills` A/B), `medication_effect` (`hx_nephrotoxin_contrast_exposure` A/B), `intraabdominal_abscess` (`hx_prior_abdominal_surgery` A/B).
- **SCOPE (POCUS)**: all six POCUS packets carry `skill_assumption`, operator level, protocol and comparator. Clean.
- **STATUS**: 8/37 ids have A/B status disagreement; in 7 the disagreement is caused by one extractor keeping an empty/OR/RR/pediatric/back-computed estimate that the other dropped. The status rule remains undefined (as in wave 1).

---

## exam_dry_axilla
- VERIFIED: McGee PMID 10086438 "dry axilla supports the diagnosis of hypovolemia (positive likelihood ratio, 2.8; 95% CI, 1.4-5.4)" [A/B est0]; Levitt 1590613 "lack of axillary sweat (P = .026)"; Eaton 8205020 resolves.
- rce_backed agreement: est[0] identical A/B (values, CI, label, level).
- Minor NUMERIC MISMATCH: setting "ED" (A) vs "mixed" (B) for the same pooled row; RCE abstract says the 4 patient studies were ED-based (A is closer).
- No other flags. Ready to promote.

## exam_dry_mucous_membranes
- VERIFIED: McGee "moist mucous membranes and a tongue without furrows argue against it (negative likelihood ratio, 0.3; 95% CI, 0.1-0.6 for both findings)" [A est0/1, B est0].
- DIRECTION (handled, verify): source reports LR for the *absent* finding (moist membranes); both store it in `lr_negative` of the dry-membranes finding — correct under DECISIONS #20 convention. A splits into two rows (membranes / furrows), B keeps one row named for membranes only; owner picks.
- NUMERIC MISMATCH (label): A `interpretation_label: rule_out` vs B `modest` for the identical LR- 0.3 — the label vocabulary has no rule.
- SCOPE (both): sunken eyes and the positive LRs (title items) unquantified because the JAMA table is unreachable — disclosed.

## exam_mottling_score
- VERIFIED: Ait-Oufella 21373821 "score 2-3 OR 16, 95% CI (4-81); score 4-5 OR 74, 95% CI (11-1,568)", kappa 0.87 (0.72-0.97), 14-day mortality 45%; Dumas 31182133 PMC Results "mottling score (OR 2.26 [95% CI, 1.72–2.97])", 259 patients, 14-day mortality 37%; Shi 2026 42258324 "OR = 2.27, 95% CI: 1.79-2.87"; Coudroy 25516087 "29% (230 of 791)", "49% (32 of 65)", "aOR 3.29".
- **STATUS / NO LOCATION (empty estimates)** (B est[0], est[1]): every numeric field null, ORs live only in the quote; `evidence_status: partially_quantified` on zero numeric fields (validator WARN). A took the opposite route: `estimates=[]`, `not_quantified`, same quotes + locations preserved in `extraction_notes`.
- **UNITS/SCOPE** (B est[0].prevalence = 0.45, est[1].prevalence = 0.37): the `prevalence` field holds the cohort's 14-day *mortality*, not disease prevalence; will feed the Bayes/renderer as prevalence.
- **Recommendation for the "no numeric field" estimates (applies also to `exam_abdominal_distension` B, `hx_prior_abdominal_surgery` B, `exam_saddle_anesthesia_anal_tone` A)**: delete them from `estimates[]` and set `not_quantified`, keeping the quote + location in `extraction_notes` exactly as extractor-A did. Rationale: spec rule 1 (no schema number → null + note); the schema has no OR/RR field, the renderer shows `estimates[]` rows as accuracy data, and an empty row with `interpretation_label: rule_in` would render as a rule-in sign with no number. If the owner wants prognostic ORs first-class, that is a schema decision (add `association_stat`), not a packet fix.
- Minor: A's Shi 2026 note "22 studies n=2,727" is not in the abstract (unlocated count); B `evidence_level: validation_cohort` for Dumas is defensible (external Brazilian validation).

## exam_nec_fasc_hard_signs
- VERIFIED: Fernando 29672405 "for hemorrhagic bullae 25.2% and 95.8%, and for hypotension 21.0% and 97.7%", "fever was 46.0% and 77.0%", 23 studies n=5982; Johari 2026 42286824 resolves (Acad Emerg Med, no abstract).
- Full agreement A/B on all three rows including computed LRs (6.0/0.78, 9.1/0.81, 2.0/0.70); computation from pooled point estimates disclosed (`computed=true`, inputs shown). CIs null because the tables are paywalled — acceptable.
- **SCOPE / COMPOSITE-adjacent** (both est[1], est[2]): "hypotension" and "fever" are not the titled hard signs (bullae, crepitus, anesthesia, spread). They will render under a record named for hard signs; crepitus/anesthesia/spread remain unquantified (both disclose).
- Minor: LRs derived from bivariate-pooled sens/spec are not the meta-analysis's own LRs; `evidence_level: pooled` is fair but note "LR derived".

## hx_rigors_shaking_chills
- VERIFIED: Coburn 22851117 "shaking chills, LR, 4.7; 95% CI, 3.0-7.2", 35 studies, 4566/25,946, immunocompromised exclusion; Tokuda 16378800 "specificity of 90.3% (95% CI 89.2-91.5) and positive likelihood ratio of 4.65 (95% CI 2.95-6.86)", "absence of chills showed a sensitivity of 87.5% (95% CI 74.4-94.5) and negative likelihood ratio of 0.24 (95% CI 0.11-0.51)", 526/40 (7.6%).
- rce_backed agreement: all three rows identical A/B (order differs).
- **POPULATION COLLAPSE** (A est[0], B est[2]): `evidence_level: pooled` for the RCE LR 4.7, but both extractors note it "coincides with"/"is largely derived from" Tokuda's single study; the RCE abstract does not say how many studies graded chills. Label single-study-equivalent until the JAMA table is checked.
- DIRECTION (verify): Tokuda's sentence "The absence of chills showed a sensitivity of 87.5%" is read by both as sensitivity of *any chills* = 0.875 with LR- 0.24 for absence; this is the sensible reading but the abstract's wording is inverted — confirm against the paper.
- VOCAB (soft, both): `cholangitis` is not listed under fever/hypotension/aki/ams in vocab.json.
- Minor: Tokuda year 2005 (print) vs PubMed 2006.

## exam_cva_tenderness
- VERIFIED: Bent 12020306 "costovertebral angle tenderness (LR, 1.7; 95% CI, 1.1-2.5)", "back pain (LR, 1.6; 95% CI, 1.2-2.1)", "absence of back pain (LR, 0.8; 95% CI, 0.7-0.9)", "probability of infection is approximately 50%".
- rce_backed agreement: CVA LR+ 1.7 identical A/B.
- **STATUS**: A `quantified` vs B `partially_quantified` on identical evidence (LR+ only, no LR-). B's reasoning (no negative LR for the sign) is the better reading; the rule is undefined.
- **SCOPE** (A est[1], est[2]; B est[1]): "back pain" history LRs are a different finding entered under the CVA-tenderness exam record; they will render as CVA-tenderness rows. Move to a history id or drop.
- UNITS/SCOPE (both, `prevalence = 0.5`): the RCE's stated pretest probability in symptomatic women, not a study prevalence; acceptable if the field is documented as pretest.
- SCOPE (both): pyelonephritis-vs-cystitis and obstruction (the record's differentials) unquantified — disclosed.

## hx_dysuria_frequency
- VERIFIED: Bent abstract "dysuria (summary positive likelihood ratio [LR], 1.5; 95% confidence interval [CI], 1.2-2.0)", "absence of dysuria (summary negative LR, 0.5; 95% CI, 0.3-0.7)", "frequency (LR, 1.8; 95% CI, 1.1-3.0)", "24.6 for the combination of dysuria and frequency but no vaginal discharge or irritation".
- rce_backed agreement: dysuria 1.5/0.5, frequency 1.8, combination 24.6 identical A/B.
- **QUOTE NOT VERBATIM** (B est[0].quote): "dysuria (summary positive likelihood ratio [LR], 1.5; 95% CI, 1.2-2.0)" — the abstract reads "95% confidence interval [CI], 1.2-2.0"; B silently abbreviated inside a quoted span and spliced two sentences with "…". Number correct; the only non-verbatim quote in the batch.
- **COMPOSITE** (A est[3], B est[2]): "dysuria AND frequency AND no vaginal discharge/irritation" (LR 24.6, single study, no CI) is a three-item combination entered under a single-symptom record; disclosed in `target_condition` and `evidence_level: single_study`, but `interpretation_label: rule_in` will render prominently.
- SCOPE (both): elderly/delirium (seeded tag and differential) unquantified — disclosed.

## exam_joint_effusion_warmth_painful_rom
- VERIFIED: Margaretten 17405973 "Joint pain (sensitivity, 85%; 95% confidence interval [CI], 78%-90%), a history of joint swelling (sensitivity, 78%; 95% CI, 71%-85%)", "fever (sensitivity, 57%; 95% CI, 52%-62%)", "Fourteen studies involving 6242 patients, of whom 653"; Carpenter 21843213 "approximately 27% (95% CI = 17% to 38%)", "+LR = 6.9", "+LR = 15.0".
- rce_backed agreement: all three sensitivity rows identical A/B.
- **SCOPE / COMPOSITE-adjacent** (both, all rows): the quantified items are "joint pain", "history of joint swelling" and "fever" — none is the titled sign (effusion, warmth, painful ROM); all are sensitivity-only, so the record cannot compute an LR. `partially_quantified` is right; consider whether these rows should render at all.
- NO LOCATION-lite (B extraction_notes / interobserver_note): Carpenter 27%, LR+ 6.9, LR+ 15.0 — verified in the abstract, so they are located, but they are numbers in prose fields not in `estimates[]`; either enter them (prevalence; two history/exam LRs with separate ids) or remove.
- Minor: Carpenter year 2011 (print) vs PubMed 2012.

## hx_nephrotoxin_contrast_exposure
- VERIFIED: Khwaja 22890468 resolves (KDIGO summary; PubMed year 2015 vs print 2012 — both note it).
- Full agreement A/B: `not_quantified`, guideline-cited per spec rule 4. Clean.
- VOCAB (soft, both): `medication_effect` is not listed under `aki` in vocab.json (it sits under dizziness/edema/hypotension/ams).

## exam_abdominal_rigidity_guarding
- VERIFIED: Becker 17192449 "lack of guarding (47%)", "lack of guarding (LR, 0.63)", "Seven hundred fifty-five patients", "36% … appendicitis", percentages are "Among patients with appendicitis" (so B's sens = 1 − 0.47 is valid); Dixon 2004144 "guarding (3.07), and muscular rigidity in the abdomen (5.03)"; Laurell 23838773 "local guarding (2.11)"; Andersson 14716790 "ROC areas of 0.78 to 0.68"; Wagner 8918857 abstract has **no numbers**.
- **FABRICATION SUSPECT (citation)** (B sources[0]): "Kharbanda AB, Taylor GA, Fishman SJ, Bachur RG. Atypical clinical features of pediatric appendicitis. Acad Emerg Med 2007" — PMID 17192449 resolves to **Becker T, Kharbanda A, Bachur R** (Acad Emerg Med 2007;14:124). The quoted author list is that of Kharbanda's 2005 Pediatrics decision-rule paper (PMID 16140712). Numbers are real; citation wrong. Same error in `exam_rebound_tenderness` B, `exam_rlq_tenderness_mcburney` B, `hx_rlq_pain_migration` B.
- **STATUS / POPULATION COLLAPSE** (B est[0], est[1]): the only numbers under this adult abdominal-pain record are pediatric (median age 11.9 y), labelled as such in `population`, yet they drive `partially_quantified` and B's `negative_finding` text ("pediatric LR- ~0.6"). A dropped everything and went `not_quantified`. Owner decision: pediatric-only evidence should probably not quantify an adult record; at minimum `target_condition` should carry "(pediatric)" as B did elsewhere.
- **NO LOCATION-lite** (A extraction_notes): "Wagner 1996 … reports rigidity LR+ ~3.8 and guarding LR+ ~2.5" — recalled from an unviewed JAMA table (wave-1 weakness 7). Same pattern in `exam_rlq_tenderness_mcburney` A/B ("LR+ ~7.3-8.5 … from memory"), `exam_rebound_tenderness` A ("LR+ ~1.1-6.3"), `hx_rlq_pain_migration` A ("LR+ ~3.1-3.4 / LR- ~0.5").
- **NOTES-DISCIPLINE** (A extraction_notes): self-contradictory — "Status therefore partially_quantified; owner should pull Table 3" followed by "removed from estimates[] … so status is not_quantified". A post-hoc cleanup left the stale sentence. Same stale-note pattern in `exam_abdominal_distension` A, `exam_rlq_tenderness_mcburney` A, `hx_prior_abdominal_surgery` A, `hx_rlq_pain_migration` A, `pocus_bladder_volume` A.

## exam_abdominal_distension
- VERIFIED: Eskelinen 7973431 "abdominal distension (yes versus no) (RR = 13.1)"; Böhner 9840308 "The six with the highest sensitivity were distended abdomen…"; Taylor 23758299 abstract names distention among "best history and physical examination predictors" without numbers.
- **STATUS / NO LOCATION (empty estimate)** (B est[0]): all numeric fields null, RR 13.1 in the quote, `interpretation_label: rule_in`, status `partially_quantified` (validator WARN). A: `not_quantified`, RR kept in notes. RR was **not** entered as an LR anywhere (good) — see the recommendation under `exam_mottling_score`: delete the row.
- NOTES-DISCIPLINE (A): stale "entered with sens/spec/LR null" sentence contradicts "removed from estimates[]".
- Minor: Böhner print 1998 vs PubMed 1999.

## exam_murphy_sign
- VERIFIED: Trowbridge 12503981 "Murphy sign (positive LR, 2.8; 95% CI, 0.8-8.6)", 17 studies; Singer 8780468 "Murphy's sign was both sensitive (97.2%) and highly predictive (93.3%) of a positive HBS yet was not documented in 35 cases".
- rce_backed agreement: both rows identical A/B (values; A/B differ only in label for est[1]).
- **SCOPE** (both est[1]): retrospective ED cohort, HIDA reference, sign undocumented in 35/100 (verification bias); sensitivity-only. B labels it `rule_out` — a sensitivity from a 65-patient documented subset with no specificity should not carry a rule-out label (A: `modest`).
- Prevalence 0.53 = 53/100 positive HBS: "53" is not in the abstract text (both packets state it) — likely from the full text; owner should confirm.
- Minor: B omits Singer DOI; A has it.

## exam_rebound_tenderness
- VERIFIED: Golledge 8659965 "100 consecutive patients with a median age of 25 years (range 4-81 years), presenting with right iliac fossa pain", "Rebound tenderness proved to be sensitive (sensitivity 0.82), specific (specificity 0.89) and accurate (accuracy 86%)"; Bundy 17652298 "rebound tenderness triples the odds of appendicitis (summary LR, 3.0; 95% CI, 2.3-3.9), while its absence reduces the likelihood (summary LR, 0.28; 95% CI, 0.14-0.55)"; Becker "absence of rebound pain (52%)"; Alshehri 7588144 "highest sensitivity (94.7%)".
- Agreement: Golledge row identical A/B (computed LR+ 7.45/7.5, LR- 0.20, `computed=true` with inputs).
- **FABRICATION SUSPECT (citation)** (B sources[1]): Kharbanda/Becker author-list error (see `exam_abdominal_rigidity_guarding`).
- NUMERIC MISMATCH: second row differs — A = Bundy pediatric pooled LRs (labelled "(children)"); B = Becker pediatric sensitivity 0.48 computed from 52% (labelled "(pediatric)"). Both verified; owner picks (Bundy is pooled and carries CIs).
- SCOPE (A interpretation.positive_finding): "spec 0.89, sens 0.82 in adults" — Golledge's cohort spans ages 4–81; "adults" overstates. A `setting: inpatient` vs B `mixed` for the same surgical-unit cohort.
- NO LOCATION-lite (A notes): Wagner "LR+ ~1.1-6.3" recalled.

## exam_rlq_tenderness_mcburney
- VERIFIED: Becker "absence of maximal pain in the right lower quadrant (32%)"; Laurell "isolated tenderness in the right iliac fossa (3.29)"; Dixon "tenderness in the right lower quadrant (odds ratio 5.09)"; Bundy "right lower quadrant pain itself (summary LR, 1.2; 95% CI, 1.0-1.5)".
- **FABRICATION SUSPECT (citation)** (B sources[0]): Kharbanda/Becker error.
- **STATUS / POPULATION COLLAPSE** (B est[0]): sole estimate is pediatric "maximal pain in RLQ" (a symptom, not McBurney-point tenderness on palpation), sensitivity only, computed from 32%; A `not_quantified`. Labelled pediatric; still the only number under an adult exam record.
- NO LOCATION-lite (both notes): Wagner RLQ-tenderness numbers recalled from memory (B says so explicitly).
- NOTES-DISCIPLINE (A): stale "entered with sens/spec/LR null" sentence.
- Minor: B cites Laurell as "Dig Surg 2013;30(3):198-206" — PubMed gives 2014;30(4-6):283-289 (A is right); B omits the DOI.

## hx_prior_abdominal_surgery
- VERIFIED: Eskelinen "previous abdominal surgery (relative risk (RR) = 12.1)"; Böhner "previous abdominal surgery" among six most sensitive; Taylor abstract "Having a previous history of abdominal surgery … were the best history and physical examination predictors".
- **STATUS / NO LOCATION (empty estimate)** (B est[0]): all-null numeric fields, RR 12.1 in quote, label `rule_in`, status `partially_quantified` (validator WARN); A `not_quantified`. Delete the row (see `exam_mottling_score`).
- VOCAB (soft, both): `intraabdominal_abscess` is not listed under `abdominal_pain` in vocab.json (it sits under fever).
- NOTES-DISCIPLINE (A): stale sentence. Minor: Böhner year.

## hx_rlq_pain_migration
- VERIFIED: Benabbas 28214369 'history of "pain migration to right lower quadrant (RLQ)" (LR+ = 4.81, 95% confidence interval [CI] = 3.59-6.44)', "Twenty-one studies … 8,605 patients with weighted AA prevalence of 39.2%"; Becker "lack of migration of pain (50%)"; Laurell "migration of pain to the right iliac fossa (2.18)"; Bundy "(LR range, 1.9-3.1)".
- Agreement: Benabbas pediatric pooled LR+ 4.81 identical A/B.
- **FABRICATION SUSPECT (citation)** (B sources[1]): Kharbanda/Becker error. B also omits Benabbas's DOI (A has 10.1111/acem.13181).
- **POPULATION COLLAPSE** (both est[0]): the record is an adult abdominal-pain history item, `evidence_status: quantified`, yet the only numbers are pediatric ED data (A's `target_condition` says "(children)", B "(pediatric)"). Both correctly declined to enter Bundy's range 1.9–3.1 as a point (wave-1 weakness 2 did not recur here).
- NO LOCATION-lite (A notes): Wagner migration LRs recalled. NOTES-DISCIPLINE (A): stale "entered with LR null … was removed".

## pocus_gallbladder_wall_stones
- VERIFIED: Ross 21401784 "pooled estimates for sensitivity and specificity were 89.8% (95% confidence interval [CI] = 86.4% to 92.5%) and 88.0% (95% CI = 83.7% to 91.4%)", eight studies, 710 subjects; Summers 20138397 "sensitivity 87% (95% confidence interval [CI] 66% to 97%), specificity 82% (95% CI 74% to 88%), positive likelihood ratio 4.7 (95% CI 3.2 to 6.9), negative likelihood ratio 0.16 (95% CI 0.06 to 0.46)", 189 scanned, 23 pathology-confirmed, 25 excluded.
- Full agreement A/B on both rows; SILENT COMPUTATION hits (A/B est[1]) are false positives — LR 4.7 is printed. Ross LRs computed by both with `computed=true` and inputs.
- **SCOPE** (both est[0]): Ross pooled accuracy is for *cholelithiasis*, not cholecystitis; disclosed in `target_condition`, and A's `positive_finding` keeps the distinction. Component-level accuracy (wall thickness, sonographic Murphy) unquantified — disclosed.
- B est[1].prevalence 0.14 = 23/164 is B's own arithmetic (189 − 25); disclosed in notes. `skill_assumption` present in both.

## pocus_bladder_volume
- VERIFIED: Lukasse 17851812 "using the clinically desired value of a 400-ml threshold, are 0.76 and 0.96"; Taylor 30325783 "sensitivity of the bladder scanner identifying catheterized PVR volumes less than 100 mL was 93.7%", "For catheter PVRs greater than 100 mL, the specificity … was 72.7%", 87 subjects; Daurat 25642660 "0.94 (95% CI, 0.88-0.98) and 0.91", cutoff 9.7 cm, ≥600 mL; Theisen 29424755 "mean difference, 5.94 mL; 95% CI, -3.8 to 15.7"; Dionne 31132655 ranges.
- **FABRICATION SUSPECT (citation)** (B sources[0]): cited as "Beacock CJ, et al. (author list per PubMed)" — PMID 30325783 resolves to **Taylor DL, Sierra T, Duenas-Garcia OF, Kim Y…** (Female Pelvic Med Reconstr Surg 2021;27:e39). "Beacock" does not appear in the record; B's own notes admit the tool did not show the first author, so the name was invented. Numbers verified.
- **NUMERIC MISMATCH**: A and B share no estimate. A: postpartum women, automated scanner, 400 mL threshold (sens 0.76/spec 0.96). B: prolapse clinic women, 100 mL threshold, sensitivity for "<100 mL" and specificity for ">100 mL" as two half-rows.
- **DIRECTION** (B est[0]): "sensitivity of the bladder scanner identifying catheterized PVR volumes less than 100 mL" defines the *positive* state as a low volume — the inverse of the record's retention question; entering it as `sensitivity` of a retention-threshold record inverts the meaning. Should be re-expressed (or dropped) with the target stated as "PVR <100 mL".
- **POPULATION COLLAPSE / SCOPE** (both): neither population (postpartum; pelvic-organ prolapse) resembles the record's targets (elderly/AKI/post-operative/cauda equina); `evidence_status: quantified` in both overstates. A's `skill_assumption` says "estimates are from scanner devices, not manual formula" — good; the technique field describes the manual formula.
- NOTES-DISCIPLINE (A): "Theisen 2020 entered as an agreement estimate … removed from estimates[]" (stale).
- Minor: Theisen pages e12-e15 (B) vs 141-145 (A); Lukasse year 2007 vs PubMed 2012 (both note it).

## pocus_hydronephrosis
- VERIFIED: Wong 29427476 "70.2% (95% confidence interval [CI] = 67.1%-73.2%) and 75.4% (95% CI = 72.5%-78.2%)", "calculated positive and negative likelihood ratios were 2.85 and 0.39", "moderate or greater hydronephrosis yielded a specificity of 94.4% (95% CI = 92.7%-95.8%)", five studies N=1,773; Gaudreau-Simard 38388747 "sensitivity of 85% (95% CI 71-94%) and specificity of 78% (95% CI 68-87%)", 65 patients/124 kidneys, prevalence 33%; Nepal 33199317 "sensitivity of 90% and a specificity of 100%"; Herbst 24630203 "sensitivity of 72.6% … specificity of 73.3% … positive likelihood ratio of 2.72 (95% CI 2.25 to 3.27), and negative likelihood ratio of 0.37", fellowship subgroup "92.7% … 4.97 (95% CI 2.90 to 8.51) … 0.08 (95% CI 0.03 to 0.23)", 144 clinicians, 670 scans.
- rce_backed agreement: Wong any-hydronephrosis and moderate-or-greater rows identical A/B. SILENT COMPUTATION hits (A/B est[0], B est[2]) are false positives — LRs printed.
- NUMERIC MISMATCH (row sets): A adds two AKI cohorts (Gaudreau-Simard, Nepal), B adds Herbst overall + fellowship subgroup. All verified; complementary — merge rather than choose.
- **SCOPE** (both): the record is "bilateral or solitary-kidney hydronephrosis in AKI"; the pooled numbers are renal-colic stone detection with any hydronephrosis as positive. B says so explicitly ("AKI use is inferred from the stone literature and should be flagged by the verifier"); A's two AKI rows partly close the gap. B's split by fellowship training (LR- 0.08 vs 0.37) is exactly the expertise stratification the HINTS records need — keep.
- Minor: Nepal QI project has no CIs (sens 0.90/spec 1.0 on an unstated n); year quirks (Wong 2018/2019, Nepal 2020/2021, Riddell 2014/2015).

## exam_face_arm_speech_cpss
- VERIFIED: Goldstein 15900010 "LR of > or =1 finding = 5.5; 95% CI, 3.3-9.1", "LR of 0 findings = 0.39; 95% CI, 0.25-0.61", "prior probability of a stroke among patients with neurologically relevant symptoms is 10%"; Kothari 10092713 "convenience sample of 171 patients from the emergency department and neurology inpatient service", "49 had a diagnosis of stroke or transient ischemic attack", "sensitivity of 66% and specificity of 87%", "88% for identification of patients with anterior circulation strokes".
- rce_backed agreement: all three rows identical A/B (Kothari LRs computed identically, `computed=true`).
- **COMPOSITE DUPLICATE (id-level)**: the identical Goldstein + Kothari rows sit under `exam_focal_neuro_deficit_screen` (both extractors flag the overlap). These are two ids for one three-item screen; recommend folding (DECISIONS #21 pattern) rather than editing packets.
- UNITS/SCOPE (A est[0].prevalence = 0.1): the RCE's *prior probability* entered as prevalence; B leaves it null with the reason. Prefer B.
- Minor: quotes are two abstract fragments joined with "…" (both disclose).

## exam_focal_neuro_deficit_screen
- VERIFIED: Goldstein/Kothari as above; GRACE-3 36453134 "general neurologic examination-five studies, 869 patients, pooled sensitivity 46.8% (95% confidence interval [CI] 32.3%-61.9%, moderate certainty) and specificity 92.8% (95% CI 75.7%-98.1%", "limb weakness/hemiparesis-four studies, 893 patients, sensitivity 11.4% (95% CI 5.1%-23.6%, high) and specificity 98.5% (95% CI 97.1%-99.2%, high)"; Kattah 2009 PMC Table 1 "General neurologic signs (including truncal ataxia) 0% 51% 0.49 (0.39–0.61)" (PAVS n=25, CAVS n=76).
- Agreement: Goldstein and Kothari rows identical A/B; A adds GRACE-3 and Kattah rows.
- **AUTHOR MISSING** (A sources[1]): PMID 36453134 cited with no authors — PubMed: Shah VP, Oliveira J e Silva L, Farah W, et al. (same omission in `exam_nystagmus_direction_changing` A, `fn_head_impulse_test` A, `fn_hints_exam` A).
- **COMPOSITE DUPLICATE (id-level)**: see `exam_face_arm_speech_cpss`. A's Kattah "general neurologic signs" row also duplicates the Kattah specificity-1.0 pattern flagged mechanically across four dizziness ids — those are different table rows (different signs), not one number reused; the mechanical flag is a false positive except for the id-level overlap.
- SCOPE (A est[3]): specificity 1.0 from 0/25 peripheral patients in a high-risk cohort, `evidence_level: single_study`, `label: rule_in` — an exact-zero denominator; consider a CI note.
- Minor: A prevalence 0.1 (RCE prior) as above.

## exam_nystagmus_direction_changing
- VERIFIED: GRACE-3 "bidirectional, vertical, direction changing, or pure torsional nystagmus are consistent with a central cause of vertigo, sensitivity 50.7% [95% CI 41.1%-60.2%, moderate] and specificity 98.5% [95% CI 91.7%-99.7%", 16 studies/1366; Tarnutzer 2023 PMC "direction-changing nystagmus on lateral-gaze test (37.3% [27.2-47.3])"; Kattah Table 1 "direction-changing horizontal nystagmus 0% 20% 0.80 (0.72–0.90)", "dominantly vertical or torsional nystagmus 0% 12% 0.88 (0.81–0.96)".
- Agreement: both Kattah rows identical A/B (A `computed=false` reading the printed %; B `computed=true` deriving sens/spec from the % — B's is the more honest flag; either is acceptable). SILENT-adjacent: none.
- AUTHOR MISSING (A sources[0]): 36453134 no authors.
- SCOPE (both Kattah rows): specificity 1.0 = 0/25; A est[1] specificity null because supplementary Table 2 was unviewable — disclosed.
- SCOPE (both): anchor RCE Froehling 1994 (8283588) has no abstract; cited without numbers — fine. Contraindications "None" is appropriate.

## fn_dix_hallpike
- VERIFIED: Halker 18469678 "A single study comparing the Dix-Hallpike and side-lying tests was identified. For the Dix-Hallpike test, the estimated sensitivity was 79% [95% confidence interval (CI) 65-94], specificity was 75% (33-100), positive likelihood ratio (LR) was 3.17 (95% CI 0.58-17.50), negative LR was 0.28 (95% CI 0.11-0.69)"; López-Escámez 10799928 "Dix-Hallpike test (SE 82%, SP 71%)", BPPV 13 patients; Hougaard 42529276 "TB diagnostics demonstrated a sensitivity of 79%, specificity of 95%, PPV of 89%, and NPV of 90%", 201 participants, 68 chair diagnoses, kappa 0.76; Cohen 15021771 abstract: 61 patients, **no sensitivity/specificity**.
- Agreement: Halker row identical A/B. SILENT hits (A/B est[0]) are false positives — LRs printed.
- **SECONDARY SOURCE** (A/B est[0], sources[0]): the numbers come from a critically appraised topic (the CAT's own estimate from an unnamed "single study … very weak methodology"), classed `meta_analysis` for want of a kind. B names the primary as Cohen 2004 (plausible, but the CAT abstract does not name it and Cohen's abstract carries no accuracy numbers); A says it could not confirm the primary. Numbers are real but the chain to a primary is unproven.
- **COMPOSITE / SCOPE** (B est[1]): Hougaard "TB diagnostics" = Dix-Hallpike *plus* supine roll test, against the same maneuvers performed in a mechanical chair (no independent standard), elderly ≥60 only; computed LR+ 15.8 from 79/95. Entered under a Dix-Hallpike-only record with `label: both`.
- NUMERIC MISMATCH (second row): A = López-Escámez (structured-history consensus standard, 13 BPPV cases); B = Hougaard. Both weak, both disclosed.
- SECONDARY SOURCE (diff report, guideline on a quantified record): AAO-HNS guideline carries no number in either packet — acceptable.

## fn_gait_stand_unaided
- VERIFIED: Tarnutzer 2023 abstract "Severe (grade 3) gait/truncal instability had high specificity 99.2% (97.8-100.0) but low sensitivity 35.8% (5.2-66.5)", Results "grade 2 or 3 gait/truncal instability (80.8% [45.1-100.0])"; Martinez 38990511 "Grade 2/3 GTI had moderate sensitivity (70.8% [95% confidence-interval (CI) = 59.3-82.3%]) and specificity (82.7 [71.6-93.8%])", "grade 3 GTI had a lower sensitivity (44.0% [34.3-53.7%] and higher specificity (99.1% [98.0-100.0%])", 18 studies/1025, Lee vs Moon 73.8% vs 57.4%; Kattah 2022 36063733 "52 patients", "92% sensitivity (95% CI 79-100%), a 67% specificity (95% CI 47-86%)"; Kattah 2009 Table 4 "Severe truncal ataxia 33% 100% 0.67 (0.56–0.79)"; Carmona 36752029 "15% (n = 14)".
- Agreement: Kattah 2022 and Kattah 2009 Table 4 rows identical A/B (B adds computed LRs 2.79/0.12 for Kattah 2022).
- **AUTHOR MISSING** (A sources[1]): 38990511 cited without authors — PubMed: Martinez C, Wang Z, Zalazar G, Carmona S, … 
- NUMERIC MISMATCH (row sets): A 6 rows vs B 2; A's four pooled rows are verified and complementary. A est[1] specificity null (supplementary table) — disclosed.
- **POPULATION COLLAPSE (overlap)** (A est[0]/est[1] vs est[2]/est[3]): Tarnutzer 2023 and Martinez 2024 pool overlapping primary studies (same group); A reports both and says so — fine, but the renderer will show two "pooled" grade-3 rows (35.8% vs 44.0% sensitivity). Owner should pick one pooled source per cut-off.
- SCOPE: contraindications and safety present in both (hypotension, obtunded, fall risk). Kattah 2022 stroke prevalence not in abstract — B leaves null (good).

## fn_head_impulse_test
- VERIFIED: Tarnutzer 2023 "Sensitivity for detecting a central cause of AVS was highest for a normal hHIT (79.9% [95% CI 72.2-87.5])", "AICA strokes were missed more frequently when applying the hHIT alone (sensitivity=36.0% [20.2-55.5])"; GRACE-3 "head impulse test (HIT)-17 studies, 1366 patients, sensitivity 76.8% (64.4%-85.8%, low) and specificity 89.1% (95% CI 75.8%-95.6%, moderate)"; Kattah Table 1 "h-HIT normal or untestable 0% 93% 0.07 (0.03–0.15)".
- Agreement: Kattah row identical A/B; A adds three pooled rows. AUTHOR MISSING (A sources[1]): 36453134.
- **DIRECTION (handled, verify)**: both packets define the positive-for-central finding as a *normal* HIT and say so in notes, `target_condition` and `pitfalls`; `sensitivity` therefore = proportion of central AVS with a normal HIT. Correct, but the renderer's "positive finding" prose must not be read as "abnormal HIT" — A's `positive_finding` describes the abnormal (peripheral) result while the estimates describe the normal result; an inconsistency the verifier should resolve in text.
- SCOPE (both est Kattah): "normal *or untestable*" (4 untestable counted as dangerous) — B discloses; A's row name includes it.
- NO LOCATION-lite (A interobserver_note): "video-HIT meta-analysis reports sens 84%/spec 85% (PMID 40447837, not cited as estimate)" — a number in prose from an uncited source.

## fn_hints_exam
- VERIFIED: Kattah Results "a dangerous H.I.N.T.S. result was 100% sensitive and 96% specific for the presence of a central lesion, giving a positive likelihood ratio of 25 (95%CI 3.66–170.59) and a negative likelihood ratio of 0.00 (95%CI 0.00–0.11)", Table 4 "Dangerous bedside H.I.N.T.S. 100% 96% 0.00 (0.00–0.12)"; Ohle 32167642 "when performed by neurologists, had a sensitivity of 96.7% (95% CI = 93.1% to 98.5%, I2 = 0%) and specificity of 94.8% (95% CI = 91% to 97.1%)", "When performed by a cohort of physicians including both emergency physicians (board certified) and neurologists … the sensitivity was 83% (95% CI = 63% to 95%) and specificity was 44% (95% CI = 36% to 51%)", 5 studies/617, prevalence mean 39.1%; Tarnutzer 2023 "subspecialists 94.3% [88.2-100.0] vs. non-subspecialists 95.0% [91.2-98.9], p=0.55 … specificity … (97.6% [94.9-100.0] vs. 89.1% [83.0-95.2], p=0.007)", "sensitivity=95.3% [92.5-98.1]; LR−=0.09 [0.05-0.17] … specificity=92.6% [88.6-96.5]; LR+=7.95 [4.94-12.78]"; Krishnan 31984230 "pooled sensitivity was 95.5% (95% CI: 92.6-98.4%) and specificity was 71.2% (95% CI: 67.0-75.4%)", 6 studies/644/200; GRACE-3 "HINTS … 14 studies, 1781 patients, sensitivity 92.9% (95% CI 79.1%-97.9%, high) and specificity 83.4%".
- **Watch-item result: PASS.** Both packets split by examiner expertise and never average: Kattah (single neuro-ophthalmologist), Ohle neurologists vs mixed EP+neurologist cohort (correctly labelled — the abstract's 83/44 cohort is *mixed*, not EP-only; both got this right), Tarnutzer subspecialist vs non-subspecialist (A only), overall pooled (A only). All rows except A est[7] are AVS-scoped; A labels the GRACE-3 row "ED population, not restricted to AVS" and keeps it separate.
- rce_backed agreement: Kattah, Ohle ×2 and Krishnan rows identical A/B in sens/spec. SILENT hits (A/B est[0]) are false positives — LR+ 25 printed.
- **SILENT COMPUTATION (disclosed, questionable)** (B est[1], est[2], est[3]): B computes LR+/LR- from pooled sens/spec of three meta-analyses (18.6/0.035, 1.48/0.39, 3.32/0.063) with `computed=true`; LRs derived from bivariate pooled sens/spec are not the meta-analyses' LRs and carry no CI. A leaves them null. Prefer A (Tarnutzer's own LR+ 7.95/LR- 0.09 are available and A entered them).
- **UNITS** (A/B est[0].lr_negative = 0.0): printed as 0.00 in the source, but a literal zero LR must be null + note per validator (WARN in both).
- AUTHOR MISSING (A sources[4]): 36453134. Minor: Ohle/Krishnan year quirks (epub vs PubMed) noted by both.
- SCOPE: B's `interobserver_note` states "the two must not be averaged or applied interchangeably" — good.

## exam_saddle_anesthesia_anal_tone
- VERIFIED: Dionne 31132655 "pooled sensitivity for the signs and symptoms ranged from 0.19 (95% CI 0.09 to 0.33) to 0.43 (95% CI 0.30 to 0.56) while the pooled specificity ranged from 0.62 (95% CI 0.59 to 0.73) to 0.88 (95% CI 0.85 to 0.92)", seven studies N=569, "from six of seven studies"; corrigenda 31300389 and 33722511 resolve; Gooding 23113877 "test accuracy 51%, diagnostic odds ratio 1.42", 57 patients; Bell 17453789 "altered perineal sensation were … 0.60"; Domen 19490073 "OR of 48.00", ">500 ml", 58 cases.
- **STATUS / NO LOCATION (empty estimate) / COMPOSITE** (A est[0]): all numeric fields null; the quote is a *range across seven different red flags* (not the two signs of this record), `label: rule_in`, `evidence_level: pooled`, status `partially_quantified` (validator WARN). B: `not_quantified`, same evidence in notes, plus the "verifier should fill from Dionne Table 3" instruction. Delete A's row (see `exam_mottling_score`); B's handling is the model.
- SCOPE: both note the two corrigenda — good; owner must use the corrected table.
- Minor: Dionne year 2019 (issue) vs PubMed 2020.

## exam_sensory_level_upper_motor_neuron_signs
- VERIFIED: Miller & Johnston 16247040 "reliability of the Babinski sign was fair (kappa 0.30) … foot tapping (kappa 0.73). Agreement with known weakness was 56% for Babinski sign and 85% for foot tapping", "Ten physicians (five neurologists and five non-specialists) examined each foot of 10 subjects"; ENLS 22956117 resolves (O'Phelan KH, Bunney EB, Weingart SD, Smith WS).
- Full agreement A/B: `not_quantified`, reliability data kept in `interobserver_note` (correct handling — kappa is not accuracy).
- AUTHOR MISSING (A sources[0]): ENLS cited without authors; B has them. B `kind: consensus` vs A `guideline` for the same ENLS protocol — both schema-valid; pick one.
- UNRESOLVABLE (B sources[2]): NICE NG234 with no PMID/DOI (validator WARN). NICE NG234 (2023) is real; add its URL or drop. Not fabricated.
- Minor: Miller year 2005 (print) vs PubMed 2006 (both note).

## hx_deliriogenic_medication_review
- VERIFIED: Inouye 8596223 "more than three medications added (RR, 2.9; 95% CI, 1.6 to 5.4)"; Clegg 21068014 "opioids (odds ratio [OR] 2.5, 95% CI 1.2-5.2), benzodiazepines (3.0, 1.3-6.8), dihydropyridines (2.4, 1.0-5.8) and possibly antihistamines (1.8, 0.7-4.5)"; Tune 8508041 resolves.
- Full agreement A/B: `not_quantified`, RR/OR kept in notes with location, none entered as LR. Clean; the model for the "no numeric field" cases.

## exam_cam_delirium_screen
- VERIFIED: Wong 20716741 "summary-positive LR, 9.6; 95% CI, 5.8-16.0; summary-negative LR, 0.16; 95% CI, 0.09-0.29", 25 studies N=3027; Shi 24092976 "pooled sensitivities and specificity for CAM were 82% (95% confidence interval [CI]: 69%-91%) and 99% (95% CI: 87%-100%)", "Twenty-two studies (n = 2,442 patients)"; Wei 18384586 "seven high-quality studies (N=1,071) … sensitivity of 94% (95% confidence interval (CI)=91-97%) and specificity of 89% (95% CI=85-94%)".
- rce_backed agreement: Wong LR row identical A/B.
- **NUMERIC MISMATCH** (A est[1] vs B est[1]): A = Shi 2013 (82%/99%, 22 studies, bivariate); B = Wei 2008 (94%/89%, 7 studies). Both verified, different pools — not an error; owner picks (Shi is later, larger and bivariate) and labels the other as superseded.
- SCOPE (both): the CAM detects delirium, not its cause; the record's seven differentials are causes. Both `pitfalls` say so. Fine.

## exam_meningeal_signs_nuchal_kernig_brudzinski
- VERIFIED: Akaishi 31516806 PMC Table 2 rows "Kernig's sign 9 1.20 78 22.9% (17.9-28.0) 91.2% (88.8-93.6) 2.61 (1.83-3.71) 0.84 (0.79-0.91)", "Brudzinski's sign 7 0.42 58 27.5% (21.5-33.4) 88.8% (85.8-91.7) 2.44 (1.74-3.44) 0.82 (0.75-0.89)", "Nuchal rigidity 9 0.51 77 46.1% (40.5-51.7) 71.3% (67.6-74.9) 1.60 (1.35-1.91) 0.76 (0.67-0.85)"; Results text confirms "simply summing up the cases from the enrolled nine studies" and 99% CIs, 599 vs 1216; Thomas 12060874 "Kernig's sign (sensitivity, 5%; … [LR(+)], 0.97), Brudzinski's sign (sensitivity, 5%; LR(+), 0.97), and nuchal rigidity (sensitivity, 30%; LR(+), 0.94)", 297 adults; Nakao 24139448 all eight percentages, 230 patients, 47 (20%) pleocytosis; Attia 10411200 "only 1 study has assessed Kernig sign; no studies subsequent to the original report have evaluated Brudzinski sign".
- SILENT COMPUTATION hits (A est[0-2]) are false positives — Table 2 prints the LRs.
- NUMERIC MISMATCH (row sets): A has Akaishi pooled rows, B does not; B splits Thomas into three rows and Nakao into three; A merges Kernig+Brudzinski (Thomas) into one row. Values agree wherever both have them.
- **SILENT COMPUTATION (disclosed, unstable)** (B est[3], est[4], est[5]): LRs computed from whole-percent sensitivities of 2% and 13% (LR+ 0.67, 1.0, 0.65; LR- 1.01, 1.0, 1.09). With sens = 2% the true LR+ could be anywhere between ~0.5 and ~1.5 (B admits "crude"). Recommend null + note; the Nakao paper's own message (signs uninformative) is what should render.
- POPULATION COLLAPSE (A est[0-2].population "9 case-control datasets"): Akaishi's Table 1 lists cohorts of suspected-meningitis patients undergoing LP (cross-sectional), not case-control studies; mislabel.
- **COMPOSITE DUPLICATE (id-level)**: Akaishi/Thomas/Nakao nuchal-rigidity rows appear again under `exam_neck_stiffness` (both extractors point there). Two ids for one sign family; fold or accept.
- SCOPE (B est[0]): row named "Meningitis (CSF ≥6 WBC/mL)" carries Kernig's numbers but the quote spans Kernig and Brudzinski; `target_condition` should name the sign (B's est[1] does).

## exam_neck_stiffness
- VERIFIED: Akaishi, Thomas, Nakao as above; Thomas "Only for 4 patients with severe meningeal inflammation (>/=1000 WBCs/mL of CSF) did nuchal rigidity show diagnostic value (sensitivity, 100%; negative predictive value, 100%)"; Attia "the absence of fever, neck stiffness, and altered mental status effectively eliminates meningitis (sensitivity, 99%-100% for the presence of 1 of these findings)".
- Agreement: Thomas nuchal-rigidity row and Nakao row identical A/B (B computes LRs 0.65/1.09 — same instability caveat as above). A adds Akaishi (verified).
- **COMPOSITE (watch-item: Attia)** (A est[4], B est[2]): the RCE's 99–100% sensitivity is for "≥1 of fever, neck stiffness, altered mental status" — a three-finding composite entered under the single-sign record. Both label it composite in `target_condition` and A's `pitfalls` warns explicitly, but it will render as a `rule_out` row (sens 0.99) on the nuchal-rigidity card. Move to a syndrome-level note, not an estimate.
- **POPULATION COLLAPSE (range-as-point)** (A est[4], B est[2] sensitivity = 0.99): "99%-100%" entered at its lower bound; B says so in notes. Wave-1 weakness 2 recurs here (once, in both packets).
- **SCOPE** (A est[2]): sensitivity 1.0 in a 4-patient subset with `interpretation_label: rule_out` — n=4 cannot support a rule-out label; keep as a note or null with n stated.
- COMPOSITE DUPLICATE (id-level): see `exam_meningeal_signs…`.

## fn_jolt_accentuation
- VERIFIED: Iguchi Cochrane 32524581 "pooled sensitivity was 65.3% (95% confidence interval (CI) 37.3 to 85.6), and pooled specificity was 70.4% (95% CI 47.7 to 86.1)", "75.2% (95% CI 54.3 to 88.6) and 60.8% (95% CI 43.4 to 75.9)"; Uchihara 2071396 "Among 34 patients with pleocytosis, 33 had jolt accentuation (sensitivity: 97.1%)", "Among 20 patients without pleocytosis, 12 had no jolt accentuation (specificity: 60%)"; Attia "sensitivity of 100%, specificity of 54%, positive likelihood ratio of 2.2, and negative likelihood ratio of 0"; Nakao "sensitivity of jolt accentuation was 21%", "specificity of jolt accentuation was 82%", 197 with headache; Akaishi Table 2 "Jolt accentuation 8 1.27 85 52.4% (46.2-58.6) 71.1% (66.7-75.5) 1.81 (1.50-2.20) 0.67 (0.58-0.77)"; Tamune 30178879 resolves (Headache 2019).
- SILENT hits (A est[3], est[5]; B est[1]) are false positives — LRs printed. Uchihara LRs computed from counts with `computed=true` in both (2.43 / 0.05).
- **FABRICATION SUSPECT (citation)** (B sources[3]): PMID 30178879 cited as "Iguchi M, Noguchi Y, Yamamoto S, Tanaka Y, Tsujimoto H. Does This Adult Patient With Jolt Accentuation of Headache Have Acute Meningitis? Headache 2019;59:159-163" — PubMed: **Tamune H, Kuki T, Kashiyama T, Uchihara T** (A cites it correctly as Headache 2019;59:1339-1346). B swapped in the Cochrane authors (Iguchi et al. = PMID 32524581, which B does not cite). B's notes even say "(Iguchi et al)".
- **POPULATION COLLAPSE** (A est[3], B est[1] `evidence_level: pooled`): Attia's 100%/54%/2.2/0 is the RCE's recalculation of the single Uchihara cohort (both packets say so in notes) — `single_study`, not `pooled`. A est[2] and A est[3]/B est[1] therefore present the same 54 patients twice with different numbers (97.1/60 vs 100/54); keep one and note the other.
- **UNITS** (A est[3], B est[1] lr_negative = 0.0): literal zero LR (validator WARN); null + note.
- NO LOCATION-lite (B est[0]): B's quote contains only the 33/34 sensitivity fragment; the specificity 0.60 (12/20) it stores is not in its quote (it is in A's). Number verified here, but B's row fails the "quote contains the number" rule for specificity.
- NUMERIC MISMATCH (row sets): A adds the Cochrane primary and consciousness-subgroup rows and Akaishi; B has only three rows. A's Cochrane rows are the best-quality evidence and should anchor the record.
- A sources[5] kind `meta_analysis` for Tamune (a review without pooling) — A discloses; `consensus` would be closer.

## fn_ice_pack_test
- VERIFIED: Scherer 15840866 "(summary positive LR, 24.0; 95% CI, 8.5-67.0)", "(summary negative LR, 0.16; 95% CI, 0.09-0.27)"; Golnik 10406606 "16 of the 20 (80%) patients with MG and in none of the 20 patients without MG".
- rce_backed agreement: est[0] identical A/B.
- NUMERIC MISMATCH: A adds the Golnik case-control row (B could not confirm the PMID — A's 10406606 resolves; B may adopt it).
- **UNITS/SCOPE** (A est[1].prevalence = 0.5): 20/40 case-control ratio in the `prevalence` field (wave-1 weakness 6 recurs; A discloses in notes). Null it.
- SCOPE (A est[1]): specificity 1.0 from 0/20 controls; LRs correctly left null. Contraindication "cold urticaria" present in both — good.

## hx_back_pain_cancer_history
- VERIFIED: Downie 24335669 PMC Results 'When present, "history of cancer" suggests a post-test probability of 7% (95% confidence interval 3% to 16%) in primary care, and 33% (22% to 46%) in the emergency setting'; Methods confirm post-test probability was "determined with … point estimate of pre-test probability and the 95% confidence interval of the likelihood ratio", pre-test "malignancy: 0.5% for primary care, 1.5% for secondary and tertiary care" (Figure 4 legend); Deyo & Diehl 2967893 "1,975 walk-in patients", "previous history of cancer" among significant predictors; Henschke 23450586, Deyo 1992 1386391 (no abstract) resolve.
- **Watch-item result (Downie back-computed LRs): arithmetic is legitimate, labelling is not.** A's LR+ 15.0 (6.2–37.9) and 32.3 (18.5–55.9) invert exactly the transformation the review states it used (fixed nominal pre-test × LR CI → post-test CI), so they recover the review's LR point estimates and CIs rather than inventing them. However: (i) `computed=true` with a derivation from a *nominal* pre-test line, not a 2×2 — spec rule 5 territory; (ii) `prevalence` fields hold the review's nominal 0.5%/1.5%, not study prevalence (Deyo & Diehl actual 13/1975 = 0.66%); (iii) the ED primary (Reinus 1998) is not confirmed by PMID; (iv) sensitivity/specificity remain null. B declined to convert and went `not_quantified` with the same quotes in notes.
- **STATUS**: A `partially_quantified` vs B `not_quantified`, reason stated by both — the clearest status disagreement in the batch; owner decides whether a back-computed LR from an OA review's text is admissible. Recommendation: admissible only if Figure 4's plotted LR values are read off and confirmed (or Henschke Cochrane Table consulted); otherwise B.
- SCOPE (both): age >50, night pain, weight loss (title items) unquantified — both disclose (Downie: post-test <3%).

## hx_palpitations_exertional_onset
- VERIFIED: Thavendiranathan 19920238 "affected by sleeping (LR, 2.29; 95% CI, 1.33-3.94), or while the patient is at work (LR, 2.17; 95% CI, 1.19-3.96)", "regular rapid-pounding sensation in the neck (LR, 177 …)"; Weber 8629647 "cardiac in 43%, psychiatric in 31%"; Zimetbaum 9571258 resolves (NEJM 1998; no abstract).
- Full agreement A/B: `not_quantified`, consensus source per rule 4. Zimetbaum is a narrative review — acceptable *only* because no number rests on it.
- NO LOCATION-lite (A pitfalls): "'palpitations while at work' (LR 2.17) and 'affected by sleeping' (LR 2.29)" — numbers in a prose field on a `not_quantified` record; verified in the abstract, but they are unlocated in the record and will surface as numbers on a card with no estimate. Move to notes.

## fn_pulse_palpation_during_symptoms
- VERIFIED: Cooke 16451780 "3 studies (2385 patients)", "Pooled sensitivity was 94% (95% confidence interval [CI], 84%-97%) and pooled specificity was 72% (95% CI, 69%-75%)", "The pooled positive likelihood ratio was 3.39, while the pooled negative likelihood ratio was 0.10".
- Full agreement A/B on values. SILENT hit (B est[0]) is a false positive — LRs printed.
- **COMPOSITE DUPLICATE (id-level, cross-wave)**: the Cooke row is identical to `exam_pulse_irregularly_irregular` (wave 1). Both packets say the titled maneuver (rate, regularity, abrupt termination *during* an episode) is unquantified and the Cooke data are screening populations — so this record's only numbers belong to another id. Either fold or set `partially_quantified` with the Cooke row cross-referenced rather than duplicated.
- SCOPE (A est[0]/est[1]): A splits one pooled analysis into two `estimates[]` rows (sens/spec in one, LRs in the other) purely to keep quotes ≤25 words; the renderer will show two rows for one estimate. Merge (B's single row is right); the 25-word rule should permit two quotes per estimate, not two estimates per quote.

---

## Suggested verification order (owner)

1. **FABRICATION SUSPECT / citation integrity** — `pocus_bladder_volume` B sources[0] ("Beacock CJ" → Taylor DL); Kharbanda→Becker author list in B ×4 (`exam_abdominal_rigidity_guarding`, `exam_rebound_tenderness`, `exam_rlq_tenderness_mcburney`, `hx_rlq_pain_migration`); Iguchi→Tamune swap in `fn_jolt_accentuation` B sources[3]; missing author lists in A (36453134 ×4, 38990511, 22956117); NICE NG234 without identifier (`exam_sensory_level…` B).
2. **DIRECTION / UNITS / disclosed computations** — `pocus_bladder_volume` B est[0] (sensitivity of "<100 mL"); literal `lr_negative = 0.0` (`fn_hints_exam` A/B est0, `fn_jolt_accentuation` A est3 / B est1); `hx_back_pain_cancer_history` A back-computed LRs and nominal prevalences; `exam_meningeal_signs…` B est[3-5] LRs from 2% sensitivities; `fn_hints_exam` B est[1-3] LRs from pooled sens/spec; `prevalence` misuse (`exam_mottling_score` B mortality, `fn_ice_pack_test` A case-control 0.5, `exam_face_arm_speech_cpss`/`exam_focal_neuro…` A RCE prior 0.1, `exam_cva_tenderness`/`hx_dysuria_frequency` pretest 0.5).
3. **STATUS + empty estimates (delete or keep decision)** — `exam_mottling_score` B, `exam_abdominal_distension` B, `hx_prior_abdominal_surgery` B, `exam_saddle_anesthesia_anal_tone` A (recommend delete + note, per extractor-A/B's own handling in the paired packet); pediatric-only quantification of adult records (`exam_abdominal_rigidity_guarding` B, `exam_rlq_tenderness_mcburney` B, `hx_rlq_pain_migration` A/B); `exam_cva_tenderness` (quantified vs partial on identical evidence); `hx_back_pain_cancer_history`.
4. **NUMERIC MISMATCH by source choice (all verified)** — `exam_cam_delirium_screen` (Shi vs Wei), `fn_dix_hallpike` est[1] (López-Escámez vs Hougaard composite), `exam_rebound_tenderness` est[1] (Bundy vs Becker), `pocus_bladder_volume` (no overlap), `fn_gait_stand_unaided` (two overlapping pooled sources), `pocus_hydronephrosis` (complementary row sets — merge).
5. **rce_backed / pooled agreements ready to promote** — `exam_dry_axilla`; `exam_dry_mucous_membranes`; `hx_rigors_shaking_chills` (re-label RCE row single-study); `exam_cva_tenderness` est0; `hx_dysuria_frequency` est0-2; `exam_joint_effusion…` (sensitivities only); `exam_nec_fasc_hard_signs` all three; `exam_murphy_sign` est0; `exam_rebound_tenderness` Golledge; `pocus_gallbladder_wall_stones` both; `pocus_hydronephrosis` Wong ×2; `exam_face_arm_speech_cpss` all; `exam_nystagmus…` Kattah ×2; `fn_head_impulse_test` Kattah; `fn_hints_exam` Kattah/Ohle ×2/Krishnan + A's Tarnutzer rows; `exam_cam_delirium_screen` Wong; `exam_meningeal_signs…` Akaishi ×3 and Thomas; `exam_neck_stiffness` Akaishi/Thomas/Nakao; `fn_jolt_accentuation` Cochrane ×2, Uchihara, Akaishi; `fn_ice_pack_test` Scherer; `fn_pulse_palpation…` Cooke; `fn_gait_stand_unaided` Kattah ×2 + pooled rows.
6. **COMPOSITE / SCOPE / id-level duplicates** — Attia triad under `exam_neck_stiffness`; Hougaard DH+roll under `fn_dix_hallpike` B; dysuria+frequency combination; Dionne all-flags range; nec-fasc fever/hypotension rows; joint pain/swelling/fever rows; cva back-pain rows; id pairs to fold (`exam_face_arm_speech_cpss`/`exam_focal_neuro_deficit_screen`, `exam_meningeal_signs…`/`exam_neck_stiffness`, `fn_pulse_palpation_during_symptoms`/`exam_pulse_irregularly_irregular`); recalled Wagner numbers in notes (5 packets); stale notes in A (6 packets); soft VOCAB cross-listings (3 pairs); year quirks.

## Batch verdict (wave 3 vs wave 1; these packets predate the prompt hardening)

Numbers remain honest: 107/108 quoted estimates were found verbatim in the abstract or PMC full text (the one exception is an abbreviated "95% CI" inside a quote), all 96 PMIDs resolve to the right papers, no OR/RR was entered as an LR, no percent/proportion or >1 error exists, and every mechanically flagged "silent computation" is a printed LR. Every Kattah 2009 table row, the Akaishi Table 2 rows, the Ann Neurol 2023 subgroup values and the Downie post-test probabilities check out against the PMC text, and the HINTS records are correctly split by examiner and scoped to AVS. Of the wave-1 weaknesses: (1) **composites under single-sign records** recurred but less often and always labelled (Attia triad, Hougaard DH+roll, dysuria+frequency, Dionne range) — the bigger version is now *id-level duplication* (three id pairs share one evidence base); (2) **range-as-point** recurred once (Attia 99–100% → 0.99, both packets) versus four in wave 1; (3) **author lists typed from memory** recurred in extractor-B (three distinct errors, six packets, one of them an invented surname), while extractor-A switched to omitting authors for three PMIDs — the AUTHORS-from-tool rule was needed; (4) **direction** — no stored-field inversion this time except the bladder-scanner "<100 mL" sensitivity, and the HIT/HINTS inverted-sign convention is handled in text; (5) **status rule undefined** — 8/37 mismatches, 7 of them caused by one extractor keeping a row the other deleted; (6) **empty estimates / case-control ratios in prevalence** recurred (5 empty rows, 1 case-control prevalence, plus 3 new misuses of `prevalence` for mortality/pretest/prior); (7) **numbers recalled from unviewed tables** recurred in `extraction_notes` (Wagner 1996 in five packets, plus a Shi 2026 study count and an uncited video-HIT meta-analysis). New in wave 3: **stale notes after post-hoc cleanup** (extractor-A in six packets describes estimates that no longer exist — a NOTES-DISCIPLINE failure that the wave-4 rule should catch), **pediatric-only evidence quantifying adult records** (four packets), **literal zero LRs** (four rows), and **one pooled analysis split into two estimates to satisfy the 25-word quote cap**. Net: the hardening rules adopted after wave 1 (DIRECTION / RANGES / COMPOSITES / ONE-NUMBER-MINIMUM / AUTHORS-from-tool / NOTES-DISCIPLINE / STATUS) target exactly what recurred here; the residual gaps they do not cover are (a) a `prevalence` field definition (study prevalence only; never pretest, mortality, or case-control ratio), (b) a rule that population age-group must match the record's presentation or the row is labelled and excluded from status, (c) "one estimate per analysis — use a second quote, not a second estimate, when the 25-word cap bites", and (d) `lr = 0` → null + note.
