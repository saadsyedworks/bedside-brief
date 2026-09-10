# Red-team review — wave 2 (34 ids, packets extractor-A / extractor-B)

Reviewer: red-team subagent. Date: 2026-09-10. Method: read all 68 packets; automated pre-checks (vocab, units, status/estimate consistency, POCUS scope fields, LR-vs-sens/spec arithmetic); ≥2 consequential estimates per id verified against PubMed abstract or PMC full text via `tools/pubmed.py` (98 batched checks + 12 targeted). This file extends `records/diff_report.md`; it does not repeat its STATUS MISMATCH / ESTIMATE SET DIFFERS rows except where judgment changes the reading.

Conventions: `A`/`B` = packet; `est[i]` = `estimates[i]`; "verified" = quote found verbatim at the stated location; units are proportions (DECISIONS #20).

Headline: **0 FABRICATION SUSPECT, 0 UNITS, 0 VOCAB VIOLATION.** Every quote checked was found verbatim (including all four PMC table rows and the two Berecki-Gisolf Table 2 rows). The problems in this wave are structural, not fabricated: composite scores entered as single-finding estimates, threshold/title mismatches, all-null "estimates", attribution errors when a systematic-review table is used as the source, and direction inconsistencies between an estimate and the record's own interpretation text.

---

## Respiratory exam

### exam_breath_sounds_unilateral_absent
- **VERIFIED**: A est[0] Htun 2019 Table 2 row (PMC6527561) verbatim; B est[0] Arts 2020 Table 3 "(Hemato) pneumathorax 5 0.71 … 113.5 (30.3, 425) 0.29" and est[1] Pneumonia row verbatim (PMC7192898).
- **SILENT COMPUTATION — cleared**: A est[0], B est[0], B est[1] LR− equals (1−sens)/spec but these LRs are printed in the source tables; `computed=false` is correct.
- **POPULATION COLLAPSE** (A, `estimates`): A carries only the primary-care pneumonia row and omits the trauma (hemato)pneumothorax pooled row that B found in an OA source; for a record whose title and differentials are pneumothorax/effusion first, A's single estimate is the least relevant target. Verifier should adopt B's est[0] (note B's own caveat: reference standard is CXR, so sensitivity is overstated vs CT).
- **SCOPE** (A+B, `estimates`): no pleural-effusion estimate in either packet although `pleural_effusion` is the lead differential and Wong 2009 RCE is cited; both explain (paywall). Card will show pneumonia numbers under an effusion/pneumothorax title unless labelled.
- **STATUS** (A partially_quantified vs B quantified): both reasoned; B's status is defensible only if the trauma row is accepted as the primary estimate.

### exam_percussion_dullness
- **VERIFIED**: Wong 2009 abstract LR+ 8.7 (2.2–33.8) and LR− 0.21 (0.12–0.37); Ebell 2020 LR+ 2.62 (1.14–5.30). A and B numerically identical.
- **DIRECTION** (A est[1] vs B est[1], `target_condition`): A labels the fremitus estimate "absence of reduced tactile vocal fremitus" (negative finding, LR− 0.21) while B labels it "reduced tactile vocal fremitus" and stores the same 0.21 as `lr_negative`. Same number, but B's target string reads as the positive finding — renderer will show "reduced fremitus: LR− 0.21", which is right only if the reader knows LR− is for absence. Use A's wording.
- **STATUS** (A partially_quantified vs B quantified): identical estimate sets; B's "quantified" with every sens/spec null and only one direction per finding is the weaker call. Owner should pick one rule for "LR-only" records and apply it across the wave (this pattern recurs in 9 ids below).
- **SCOPE** (A+B, `technique.contraindications` = "None."): acceptable.

### exam_egophony
- **VERIFIED**: Ebell 2020 LR+ 6.17 (1.34–18.0). A ≡ B.
- **SCOPE** (A+B): title includes "bronchial breath sounds"; neither packet quantifies it, both say so. Fine.
- No further flags; this pair is the cleanest in the batch.

### exam_wheezing
- **VERIFIED**: Straus 2000 abstract LR 2.7 (1.7–4.2); B est[1] Arts Table 3 "Obstructive lung disease 10 0.26 … 3.6 (1.9, 6.8) 0.79"; B est[2] "Congestive heart failure 4 0.21 … 0.7 (0.5, 1.0) 1.12" verbatim.
- **SILENT COMPUTATION — cleared**: diff_report's flag on B est[2] is a false positive; Arts prints the LRs.
- **DIRECTION** (B est[2], correct but needs labelling): wheeze for CHF has LR+ 0.7 / LR− 1.12 — the *presence* of the finding lowers CHF probability. `interpretation_label=minimal` is right; make sure the renderer does not present LR+ 0.7 as a rule-in row.
- **POPULATION COLLAPSE** (A, `estimates`): A has one single-study LR (CARE-COAD1) and misses the OA pooled rows B found; A's status partially_quantified is honest but the omission is an extractor-thoroughness failure, not a data gap.
- **NO LOCATION** (A est[0] + B est[0], `prevalence=0.52`): prevalence not in the quoted abstract sentence and not evidenced; both packets assert it. Verifier: confirm from CARE-COAD1 abstract or null it.

### exam_tachypnea_rr_gt24
- **VERIFIED**: A est[0] Htun Table 2 "Respiratory rate ≥ 20 min−1¥ 6 4,468 0.29 (0.10–0.59) 0.91 (0.75–0.97) 3.47 (1.46–7.23) 0.77 (0.50–0.95)"; B est[0] Marchello Table 3 "Any abnormal vital signs 0.89 (0.79 to 0.94) 0.49 (0.25 to 0.73) 1.84 (1.25 to 3.03) 0.24 (0.17 to 0.34)" (PMC7422644); Ebell LR− 0.25 (0.11–0.48).
- **DIRECTION — threshold mismatch with title** (A est[0]): record title is RR >24–25/min; A's only RR-specific estimate is pooled at ≥20/min (two studies ≥24, one ≥22). A discloses it in `extraction_notes` but the estimate's `target_condition` string is the only place the threshold appears; the card threshold will be wrong unless the verifier relabels.
- **SCOPE — composite ≠ discriminator** (A est[1], B est[0], B est[1]): "any abnormal vital sign (temp/HR/RR)" is a composite, not tachypnea. Three of the four estimates in this pair are composites.
- **STATUS** (A quantified vs B partially_quantified): B's is the correct call — no estimate in either packet isolates RR >24. Accept B's status; keep A's Htun row as the closest RR-specific number with the threshold caveat.

---

## POCUS

All 8 POCUS ids: `safety_scope.skill_assumption` present in both A and B (16/16). Operator level, protocol, threshold and comparator (spec rule 6) are present in `population`/`reference_standard` text for every estimate except where flagged below.

### pocus_lung_sliding_absent
- **VERIFIED**: Alrajhi 2012 90.9% (86.5–93.9)/98.2% (97.0–99.0); Lichtenstein 2008 A′-profile 81%/100% (n=9); Netherton 2019 eFAST 69%/99%; Ding 2011 clinician subgroup 0.89/0.99; Griffiths 2021 HEMS 61% (27–87%)/99%.
- Operator-expertise split: **present** in B (Alrajhi mixed → Ding non-radiologist → Lichtenstein single expert → Griffiths novice prehospital, sensitivity 0.91→0.89→0.81→0.61). A has the trauma eFAST row instead; B relegates it to notes. Verifier: merge — the B ladder plus A's eFAST row is the best card.
- **NO LOCATION** (A est[1] `prevalence=0.035`): 9/260 computed from a cohort that excluded uncertain diagnoses; B explicitly declines to enter it for that reason. Null it.
- **SCOPE** (A+B est[0], `population`): Alrajhi row lacks an explicit operator level in `population` ("mostly emergency physicians/intensivists" in B; absent in A). Rule 6 marginal.
- LR computed from pooled sens/spec, `computed=true` with inputs shown in both — correct handling.

### pocus_lung_b_lines
- **VERIFIED**: Maw 2019 0.88 (0.75–0.95)/0.90 (0.88–0.92); Al Deeb 2014 94.1% (81.3–98.3)/92.4% (84.2–96.4); Lichtenstein B-profile 97%/95%.
- **NO LOCATION** (A est[1] `prevalence=0.246`): same BLUE-cohort denominator problem as above; B nulls it. Null it.
- **NO LOCATION** (B est[1] `specificity.ci`): the spec CI (0.842–0.964) is in the abstract but B truncated the quote to 25 words so the CI is not in the quote; B discloses. Acceptable, but the quote-length rule is producing systematic CI-drop in this wave (see also hx_pain_abrupt A).
- **POPULATION COLLAPSE** (A+B est[0], `reference_standard`): Maw pools studies referenced against expert chart review (5) and echo+BNP (1); both packets say so. OK.
- Threshold recorded (Volpicelli ≥3 B-lines/≥2 zones bilateral) in B; A only in notes. Prefer B.

### pocus_ivc_collapsibility
- **VERIFIED**: Long 2017 0.63 (0.56–0.69)/0.73 (0.67–0.78); Orso 2020 sens 0.71 (0.62–0.80)/spec 0.75 (0.64–0.85) — the abstract lists AUC 0.71, log-DOR 2.02, sens 0.71, spec 0.75 in that order, and both packets took the 3rd/4th values correctly; B est[2] Airapetian Table 5 "cIVC > 42 % 31 % 97 % 9 0.7 90 % 59 %" verbatim (PMC4643539).
- **SILENT COMPUTATION — cleared** (B est[2]): LR+ 9 / LR− 0.7 are the authors' rounded values printed in Table 5.
- **SCOPE — title vs estimates** (A+B): title is "IVC diameter and respiratory collapsibility" (i.e. RAP estimation and volume status); every estimate is for *fluid responsiveness* against a fluid-challenge reference. The RAP use case (2.1 cm / 50% ASE cut-offs) that the card's `interpretation` text relies on is cited to no source in A and only narratively in B. Either cite the ASE guideline as a `guideline` source or strip RAP thresholds from `interpretation`.
- **NUMERIC MISMATCH** (A est[1] `setting=ICU` vs B est[1] `setting=mixed`): Orso pooled critically ill incl. children; trivial, pick one.
- **POPULATION COLLAPSE** (A+B est[0]): Long 2017 pooled ventilated + spontaneously breathing, adults + children; both note ventilated subgroups performed better but neither splits (not in abstract). B's est[2] partially fixes this for spontaneous breathers. Flag for verifier with journal access.

### pocus_pericardial_effusion
- **VERIFIED**: Mandavia 2001 96% (90.4–98.9)/98% (95.8–99.1); Netherton eFAST 91%/94%; Merce 1999 "90% and 65% for any collapse … 60% and 90% for right ventricular collapse".
- **DIRECTION — reversed reference standard** (B est[2], est[3]): Merce's sens/spec are of echo chamber-collapse signs *against clinical tamponade as the standard* (the design is inverted: echo is the usual reference). B discloses in notes but stores them as ordinary sensitivity/specificity with `interpretation_label` rule_in / rule_out. These must be labelled "concordance with clinical tamponade", not accuracy, or dropped.
- **NO LOCATION** (B est[2]/est[3] `prevalence=0.35`): 38/110 clinical-tamponade prevalence within an effusion cohort; not in the quote. Null or cite.
- **SCOPE** (A+B): title includes RA/RV diastolic collapse for tamponade; A has no tamponade estimate (states so); B's only tamponade data is the reversed-design Merce study. Effectively not_quantified for the tamponade half.
- Operator level present (ED physicians trained in US); protocol (subxiphoid/PLAX) present; threshold (effusion presence) present.

### pocus_dvt_compression
- **VERIFIED**: Pomero 2013 96.1% (90.6–98.5)/96.8% (94.6–98.1); Hercz 2024 Results text "pooled sensitivity and specificity … 90% (82–95%) and 95% (91–97%) … LR 19.1 (10.2–35.8) and 0.10 (0.06–0.19) (data not shown)" and "Two-point CUS … specialist EPs … 88% compared to the 95% found for three-point CUS … (P = 0.02)" (PMC full text); Hercz abstract specialist 93% (88–97) vs trainee 77% (60–94); Lee 2019 2-point 0.91 (0.68–0.98)/0.98; Zaki 2024 2-point 92.32% (87.58–97.06)/96.86% (95.09–98.64).
- Operator-expertise split: **present in A** (est[2] specialists vs est[3] trainees — this is exactly the watch-item), **absent in B** (B's rows say "attending or resident" without splitting). Prefer A's operator ladder; B's protocol split (2- vs 3-point, Lee 2019) is complementary.
- **NO LOCATION** (A est[1]): quote contains only the LRs; sens 0.90 / spec 0.95 are in the *preceding* sentence, not in the quote. Fix the quote (both numbers fit in 25 words).
- **NO LOCATION** (A est[4] `specificity=null`, `sensitivity=0.95`): the 2- vs 3-point sentence gives only sensitivity; correct as entered, but `population` field carries the P-value and 2-point value as free text — move to notes.
- **NUMERIC MISMATCH** (A est[1] Hercz 15 studies/2,511 exams vs B est[3] Zaki 26 studies): not a conflict — different meta-analyses — but the owner should choose one "updated pooled" row, not stack three overlapping meta-analyses (Pomero ⊂ Hercz ⊂ Zaki share primary studies).
- B est[0] `reference_standard` "…or angiography": Pomero says venography; "angiography" is a paraphrase. Minor.

### pocus_aaa_aorta_diameter
- **VERIFIED**: Rubano 2013 99% (96–100)/98% (97–99); Concannon 2014 0.975 (0.942–0.992)/0.989 (0.979–0.995).
- **NO LOCATION** (A+B est[0] `prevalence=0.23`): "weighted average 23% in symptomatic patients >50" not in the quoted sentence; both assert it from the abstract. Verifier: confirm it is in the abstract or null.
- **STATUS/labelling** (B est[1]): Concannon pools screening + symptomatic and non-ED operators; B's `setting=mixed` and population string are correct — good rule-6 compliance.
- A computed LR+ 49.5 / LR− 0.01 `computed=true` with inputs; B declined to compute. Either is fine; do not show LR− 0.01 without its (uncomputed) CI — the point estimate implies near-perfect rule-out from 7 small studies.
- Threshold (≥3 cm), protocol (transverse sweep), comparator present. Clean.

### pocus_rv_dilation
- **VERIFIED**: Dresden 2014 sens 50% (32–68), spec 98% (95–100), "LR 29 (95% CI 6.1% to 64%) and 0.51 (95% CI 0.4% to 0.7%)" — the stray "%" on the LR CIs is in the source abstract; both packets transcribed as ratios and said so (correct). Fields 2017 "Undefined 'right heart strain' … 53% (45–61) … 83% (74–90)".
- **Watch-item (Fields/Dresden definitions)**: both packets keep the two definitions separate (Dresden RV:LV >1:1 by EP; Fields "undefined right heart strain" pooled across sign definitions) and neither averages them. Good. Neither quantifies McConnell or septal flattening (Dresden 6/6 and 8/8 too few; Fields per-sign tables paywalled) — the title lists three signs, one is quantified.
- **NO LOCATION** (A est[0]): quote is the LR sentence; sens/spec are in the preceding sentence (A says so in `location`). B has the reverse (quote = sens/spec, LRs not in quote). Merge: both sentences fit in two ≤25-word quotes; use two estimates or one 25-word quote with the four numbers.
- **NUMERIC MISMATCH** (A est[1] `interpretation_label=modest` vs B est[0] `rule_in` for the same Fields LR+ 3.1): modest is correct for LR+ 3.1.
- **POPULATION COLLAPSE** (A+B, Fields row): pooled across ED/ICU/cardiology operators and sign definitions; both disclose. Acceptable with label.

### pocus_lv_function_eyeball
- **VERIFIED**: Albaroudi 2021 "89% (80–94%), 85% (80–89%), 5.98 (4.13–8.68) and 0.13 (0.06–0.24)"; McKaigney 2014 EPSS >7 mm 100.0% (62.9–100.0)/51.6% (38.6–64.5); Schick 2023 sentence verbatim; Bahl 2022 "EP1 85% and EP2 93%"; Moore 2002 kappa 0.61.
- **SILENT COMPUTATION — cleared** (A est[0]): diff_report flag is a false positive; Albaroudi prints the LRs.
- **POPULATION COLLAPSE / omission** (B, `estimates`): B does not cite Albaroudi 2021 at all — the only pooled estimate for the record's primary finding (visual LVSF) — and instead stacks five single-centre rows with three different thresholds. B's est[0] (Moore) has all-null stats.
- **STATUS** (B est[0]): an agreement statistic (kappa) entered as an `estimates[]` row with every accuracy field null. Spec rule 1 says null the estimate and explain in notes, not create an all-null row. Same pattern in hx_dizziness A, cellulitis B, hx_vte A.
- **DIRECTION / attribution ambiguity** (B est[3]): the Schick sentence "MAPSE demonstrated lower sensitivity than EPSS (79% …, 76% …) and higher specificity than estimated LVEF (100% …, 59% …)" — B assigns 79/76 to EPSS >10 mm and 100/59 to visual LVEF (parallel reading). Abstract confirms EPSS threshold >10 mm. The parenthetical could equally be MAPSE's own values; verifier must read the results table before this row is used.
- **NUMERIC caution** (A est[1]): computed LR− = 0.0 from sens 1.00 (CI 0.63–1.00, n small). A `computed=true` with inputs, so rule-compliant, but an LR− of exactly 0 must not be rendered; either null it or show the CI-bounded range.
- Operator level present throughout (fellows/credentialed EPs; Bahl per-reader). Good.

---

## VTE / aorta / GI

### hx_vte_risk_factors
- **VERIFIED**: Goodacre 2005 "malignancy (LR 2.71), previous DVT (LR 2.25), recent immobilization (LR 1.98), difference in calf diameter (LR 1.80), and recent surgery (LR 1.76) … absence of calf swelling (LR 0.67) or difference in calf diameter (LR 0.57)"; West 2007 "current DVT (2.05), leg swelling (2.11), sudden dyspnoea (1.83), active cancer (1.74), recent surgery (1.63)".
- **STATUS** (A est[5]): Wells 2006 RCE prevalence-by-category row with all-null sens/spec/LR — an all-null "estimate". Move to notes.
- **SCOPE — composite ≠ discriminator** (A est[4]): Wells *score* high/low LR 5.2/0.25 is a composite of the items the record describes plus others; should not sit beside item LRs as if it were one.
- **NO LOCATION** (A+B all Goodacre rows): no CIs in the abstract; both correctly null the CIs. Verifier with journal access: Goodacre Table 2.
- B's PE-side items (West 2007) are a genuine addition A lacks; B's `evidence_level=pooled` is right. Adopt B's set minus nothing; drop A est[4]/est[5].
- Minor: B src[1] `year=2007` vs notes "West 2008" (QJM Dec 2007 issue; both defensible).

### exam_calf_asymmetry_gt3cm
- **VERIFIED**: Goodacre 2005 LR 1.80 (difference in calf diameter) and 0.57 (absent).
- **NO LOCATION — stitched quote** (A est[0]): quote is "difference in calf diameter (LR, 1.80) ... difference in calf diameter (LR, 0.57) was useful for ruling out DVT" — two non-contiguous fragments joined with an ellipsis and presented as one verbatim quote. Not verbatim. B splits the two directions into est[0]/est[1] with contiguous quotes — use B's.
- **DIRECTION — threshold mismatch with title** (A+B): title fixes ">3 cm at 10 cm below tibial tuberosity"; Goodacre's abstract says only "difference in calf diameter". Both disclose; the card threshold is not evidenced by the cited number.
- **STATUS** (A partially_quantified vs B quantified): identical evidence (LR-only, no CI, no sens/spec, threshold unproven). Partially_quantified is the honest call.
- **SCOPE** (A+B): "with calf tenderness" in the title is unquantified in both.

### pocus_dvt_compression — see POCUS section.

### hx_pain_abrupt_maximal_onset
- **VERIFIED**: Klompas 2002 "sudden onset (sensitivity, 84%) … negative likelihood ratio [LR], 0.3; 95% CI 0.2–0.5"; Ohle case-control "Absence of abrupt-onset pain (sensitivity = 95.9%, negative likelihood ratio = 0.07 [0.03–0.14])".
- **NUMERIC MISMATCH** (A src[1] `year=2019` vs B `year=2018`): PMID 29218798 is Acad Emerg Med 2018;25(4). A is wrong.
- **NO LOCATION** (A est[0] `lr_negative.ci`): A trimmed the CI out of the quote to meet 25 words and parked it in `location`; B's quote (28 words) includes it. The 25-word rule is again forcing CI loss; B's over-length quote is the better record.
- **POPULATION COLLAPSE — spectrum** (A+B est[1]): case-control (194 cases vs 776 controls) — both flag inflated accuracy. Keep the label; do not average with Klompas.
- **DIRECTION** (A+B): both estimates are rule-out (absence of abrupt onset); no LR+ anywhere for the *positive* finding the title names. Card must not imply a rule-in value.
- A and B numerically identical otherwise.

### exam_pulsatile_abdominal_mass
- **VERIFIED**: Lederle 1999 "3.0 cm or greater are 12.0 (7.4–19.5) and 0.72 (0.65–0.81) … 4.0 cm or greater are 15.6 (8.6–28.5) and 0.51 (0.38–0.67)"; "29% for AAAs of 3.0 to 3.9 cm to 50% for AAAs of 4.0 to 4.9 cm and 76% for AAAs of 5.0 cm or greater"; Fink 2000 68% (60–76)/75% (68–82)/LR+ 2.7 (2.0–3.6)/LR− 0.43 (0.33–0.56).
- **Watch-item (Lederle strata not averaged)**: both packets keep the ≥3.0 and ≥4.0 cut-off LRs and the size-stratified sensitivities as separate rows — correct.
- **POPULATION COLLAPSE / omission** (B, `estimates`): B has 3.0–3.9 and ≥5.0 strata but drops the 4.0–4.9 cm stratum (50%) even though its own est[2] quote contains it. A has all three.
- **SILENT COMPUTATION — cleared** (B est[4]): diff_report flag false positive; Fink prints the LRs.
- **POPULATION COLLAPSE** (A+B): all Lederle rows are asymptomatic screening populations; both say so and neither has symptomatic/rupture data (none exist). The card should say "screening population".
- B est[4] `prevalence=0.495` is the case-control design fraction (99/200), not a prevalence; null it or label.

### pocus_aaa_aorta_diameter — see POCUS section.

### exam_melena_rectal_exam
- **VERIFIED** (full abstract read): "history of melena (LR range, 5.1–5.9), melenic stool on examination (LR, 25; 95% CI, 4–174) … the presence of blood clots in stool (LR, 0.05; 95% CI, 0.01–0.38) decreases the likelihood of a UGIB". A ≡ B.
- **DIRECTION** (A+B est[2]): LR 0.05 for the *presence* of clots is stored in `lr_positive` with `interpretation_label=rule_out`. Semantically right (it is the LR of the positive finding) but a renderer that prints "LR+ 0.05" under a melena card will confuse; both packets explain in `target_condition`. Keep, but the renderer needs a "finding present argues against" affordance.
- **NUMERIC caution** (A+B est[1]): reported-melena LR is a *range* 5.1–5.9; both entered the lower bound as a point value with no CI. Prefer null value + range in notes, or `value=5.1, ci_high=5.9` with a "range not CI" note (both packets' notes already say this).
- **SCOPE** (A+B): title includes hematemesis; no hematemesis estimate in either (both say so).

---

## Syncope / palpitations / dizziness

### hx_palpitations_before_syncope
- **VERIFIED** (Berecki-Gisolf 2013 Table 2, PMC3815402): "Palpitations Yes 11 1 13 4 1 9 - 39 (8%) 26 8 38 2 7 119 - 200 (11%) 3.4 1 0.06 1.03 / No 67 47 103 40 33 139 - 429 (92%) … 1568". Row sums: 39+429 = 468 cardiac; 200+1568 = 1768 non-cardiac. A's `computed_from` (sens 39/468 = 0.083, spec 1568/1768 = 0.887, LR+ 0.74) is arithmetically correct and `computed=true` with inputs shown — rule 5 compliant.
- **DIRECTION — estimate contradicts interpretation** (A, `estimates[0]` vs `interpretation.positive_finding`): the sole estimate says palpitations have LR+ 0.74 (argue *against* cardiac syncope; paper excluded the variable as non-significant, p = 0.06), while `positive_finding` says palpitations "raise concern for arrhythmic syncope (EGSYS +4)". The card would show a rule-in narrative over a <1 LR. Either drop the estimate (B's not_quantified) or rewrite the interpretation.
- **STATUS** (A quantified vs B not_quantified): B did not find the OA Berecki-Gisolf table; A did. But "quantified" on a single non-significant, direction-inverted, literature-pooled count is over-claiming; partially_quantified with the direction caveat is the honest label.
- **POPULATION COLLAPSE** (A est[0]): counts summed across 6 heterogeneous derivation cohorts (Italy/Switzerland/Canada/USA, cardiac-syncope prevalence 5–21%); naive pooling. Label as such.
- **SECONDARY SOURCE — cleared**: Berecki-Gisolf is a literature-based model built from published counts, cited as `meta_analysis`; acceptable, but it is one step removed from the primary cohorts.

### hx_post_event_confusion
- **VERIFIED**: Hoefnagels 1991 "seizure five times more likely than syncope if the patient was disoriented after the event" and "The likelihood ratio was used to calculate the predictive power of single findings" (so LR = 5 is supported); Brigo 2012 "sensitivity 33%, specificity 96%, pLR 8.167 (2.969–22.461) and nLR 0.695 (0.589–0.82)"; Benbadis 1995 24%/99%; Sheldon 2002 94%/94%.
- **SILENT COMPUTATION — cleared** (A est[1] / B est[0]): Brigo prints the pooled LRs.
- **NO LOCATION** (A est[0] / B est[2]): `lr_positive=5.0` from the words "five times more likely" — no numeral in the quote, no CI, and the abstract does not say the 5 is the LR (it says LRs were used). Keep with a "numeral inferred from prose" note.
- **SCOPE — composite ≠ discriminator** (B est[3]): Calgary point score 94/94 is a composite of ≥7 items; B labels it COMPOSITE in `target_condition`, which is the right way to do it if it must stay.
- **POPULATION COLLAPSE** (A est[2]/B est[1] vs A est[3]): Benbadis "any" vs "lateral" tongue biting — A separates (est[3] lateral, spec 1.0, sens null); B enters only "any". Title names *lateral* tongue biting; A's split is required.
- **NUMERIC MISMATCH** (A src[1] `year=2012` vs PubMed 2013 for Brigo; A's own note says so). Trivial.
- B src[0]/[1]/[2] `doi=null` where A has DOIs — B under-filled identifiers.

### hx_syncope_supine
- **VERIFIED** (Table 2): "Supine syncope Yes 9 2 - 6 - - - 17 (10%) 6 0 - 6 - - - 12 (2%) 18.1 1 <0.0001 4.23 / No 69 46 - 38 - - - 153 (90%) 253 32 - 210 - - - 495 (98%)". 17+153 = 170; 12+495 = 507. A's `computed_from` (sens 0.10, spec 0.976, LR+ 4.23 as printed, LR− 0.92 computed) is correct and rule-5 compliant.
- **STATUS** (A quantified vs B not_quantified): B missed the OA table (same as above). A's number is real. But: **POPULATION COLLAPSE** (A est[0]) — only 3 of the 7 derivation cohorts reported supine syncope; counts summed across them. Label "literature-pooled counts, 3 cohorts".
- **SCOPE** (A+B): title is "supine *or seated* without warning"; only supine is quantified.
- B cites Sheldon 2006 Calgary vasovagal score (composite) as context only — good restraint.

### hx_palpitations_abrupt_onset_offset
- **VERIFIED**: Thavendiranathan 2009 "No other features significantly alter the probability of clinically significant arrhythmia"; Weber 1996, Hoefman 2007 resolve by PMID.
- A ≡ B: not_quantified, both cite the RCE's null statement. No flags. Note for owner: neither packet could read the RCE Table 2 to confirm onset pattern was analysed; "not_quantified" here means "not visible", not "studied and null".

### hx_neck_pounding_frog_sign
- **VERIFIED**: "regular rapid-pounding sensation in the neck (LR, 177; 95% CI, 25–1251)"; absence "LR, 0.07; 95% CI, 0.03–0.19"; "visible neck pulsations (LR, 2.68; 95% CI, 1.25–5.78)".
- **Watch-item (LR 177 CI)**: both packets store ci_low 25 / ci_high 1251 — correct. Card must render the CI; a bare "LR 177" is the single most over-confident number in the store.
- **NUMERIC MISMATCH** (A `evidence_level=single_study` vs B `pooled`): the RCE abstract attributes this to a single EP study (Gürsoy 1992); A is right, B is wrong.
- **POPULATION COLLAPSE — spectrum** (A+B): population is patients with *documented paroxysmal SVT* at EP study, target is AVNRT vs other SVT — not "patients with palpitations". Both say so in `population`; the `target_condition` in A ("in patients with palpitations") overstates. Use B's target wording with A's evidence_level.
- Gürsoy 1992 (NEJM brief report, no abstract) cited without numbers — correct.

### fn_tap_out_rhythm_regular
- Both not_quantified; sources resolve (Zwietering 1998, Hoefman 2007). diff_report "agree — 0 flags" stands. **SCOPE** note only: Zwietering 1998 (762 GP patients, transtelephonic ECG) studied "patient's description of the rhythm" — B cites it but did not read the abstract for a regularity item; a verifier with the paper may find a number.

### hx_dizziness_timing_triggers
- **VERIFIED**: Newman-Toker 2007 "52% picked a different response on retest approximately 6 minutes later"; Herr 1989 "86% of 'serious' dizziness with 42% specificity"; Kerber 2006 "3.2% (53 of 1666)" and "0.7% (9 of 1297)".
- **STATUS** (A est[0]): a test-retest reliability figure entered as an `estimates[]` row with all accuracy fields null. Move to notes (B did exactly that).
- **SECONDARY SOURCE** (A src[1] + B src[2]): TiTrATE (Newman-Toker & Edlow 2015, Neurol Clin) is a narrative review, entered as `kind=consensus`. Rule 2: it is not a guideline or consensus statement; either cite it honestly as narrative context outside `sources[]` or find a guideline (e.g. AAN/ACEP dizziness guidance).
- **SCOPE — composite ≠ discriminator** (A est[1]): Herr 1989 "older age OR lack of vertigo OR neuro deficit" composite entered for a record about timing/triggers.
- **SILENT COMPUTATION — compliant** (B est[0]): 2×2 rebuilt from abstract counts (44/53 vs 1288/1613), `computed=true`, inputs shown; arithmetic checks. But the finding ("non-isolated dizziness" = any accompanying symptom/sign) is again not the title's discriminator (timing/triggers). Neither packet quantifies timing or triggers at all — this record is effectively not_quantified for its named finding; both statuses (partially_quantified) are generous.
- **NUMERIC MISMATCH** (sources): A cites Kerber 2015 (Neurology), B cites Kerber 2006 (Stroke); different papers, no shared estimate.

### hx_postural_dizziness
- **VERIFIED**: McGee 1999 "sensitivity for moderate blood loss of only 22% (6%–48%) but … large blood loss of 97% (91%–100%); the corresponding specificity is 98% (97%–99%)". A ≡ B numerically; LRs `computed=true` with inputs in both.
- **SCOPE — composite ≠ discriminator** (A+B, both estimates): the RCE finding is "severe postural dizziness *OR* pulse increment ≥30/min"; title is severe postural dizziness alone. Both disclose in `target_condition`. The card must carry the OR.
- **POPULATION COLLAPSE — spectrum** (A+B): healthy volunteers phlebotomised; not ED patients. Both say so; `setting` differs (A mixed, B outpatient) — **NUMERIC MISMATCH** trivial.
- **NO LOCATION** (A est[1] `specificity=0.98`): spec 98% is quoted once for the finding and applied to both strata; A's `computed_from` says so. Acceptable.

---

## Liver / alcohol

### exam_cirrhosis_stigmata
- **VERIFIED**: Udell 2012 "spider nevi (LR, 4.3; 95% CI 2.4–6.2)", "ascites (LR, 7.2; 95% CI, 2.9–12)", "absence of hepatomegaly (LR, 0.37; 95% CI, 0.24–0.51)".
- **SCOPE — off-title estimates** (A est[1], est[2]): ascites and hepatomegaly are not stigmata; they belong to other records (ascites ids; no hepatomegaly id). B correctly restricted to spider nevi.
- **SCOPE** (A+B): palmar erythema, gynecomastia, caput medusae, jaundice — all in the title, none quantified (paywalled tables). Both say so. Card will show only spider nevi.
- STATUS agree (partially_quantified). Prevalence 0.24 (A+B) — pooled prevalence, not in the quoted sentence; **NO LOCATION** minor.

### exam_shifting_dullness / exam_ascites_flank_dullness_fluid_wave  (DECISIONS #21)
- **VERIFIED**: Simel 1988 "fluid wave = 9.6 and shifting dullness = 5.76 … absence of bulging flanks (negative likelihood ratio = 0.12) or peripheral edema (negative likelihood ratio = 0.17)"; "overall clinical evaluation … 37.7–83.3 when suggestive". Williams 1992 and Cattau 1982 resolve by PMID (no abstracts).
- **Duplication confirmed**: A's four estimates are byte-identical across the two ids; B's four estimates are byte-identical across the two ids. Both extractors independently produced one evidence base for two cards. Supports the #21 fold.
- **SCOPE — off-title** (B est[3] both ids): "absence of peripheral edema LR− 0.17" is not an ascites exam sign.
- **SCOPE — composite ≠ discriminator** (A est[3] both ids): "overall clinical evaluation suggestive of ascites, LR+ 37.7–83.3" is the examiner's gestalt, not a sign; and A entered the *lower bound of a range across examiners* as a point value (same pattern as melena est[1]).
- **NO LOCATION / NUMERIC MISMATCH** (A `reference_standard="Abdominal ultrasonography"` vs B `"Not stated in abstract"`): the abstract does not name the reference standard; A asserted it (it is historically correct, but not evidenced from the cited location).
- **SCOPE** (A+B): flank dullness — first item in the flank-dullness id's title — has no estimate in either packet (Cattau ">90% accuracy" not entered). 
- **STATUS** agree (partially_quantified). No CIs, no sens/spec anywhere; RCE pooled table unreadable. Verifier with JAMA access: Williams 1992 Table.

### hx_alcohol_use_withdrawal_timing
- **VERIFIED**: Aertgeerts 2004 "cutoff ≥2, the pooled sensitivity is far better in inpatients (0.87) than in primary care patients (0.71) or ambulatory patients (0.60)"; "overall LR+:3.44;LR-:0.18". Kitchens 1994 resolves (no abstract).
- **SCOPE — title vs estimates** (A+B): every estimate is CAGE for *alcohol abuse/dependence*; the title's discriminating content — time since last drink, tremor/diaphoresis/agitation as withdrawal markers vs other AMS — is unquantified in both. This record is not_quantified for its stated purpose and quantified for a different question (screening).
- **STATUS** (B quantified): B has sensitivities with no specificities and an LR pair with no sens/spec; "quantified" is over-claimed. A's partially_quantified is right. (diff_report noted the mismatch; this is the reason.)
- **SECONDARY SOURCE** (B src[4] ASAM 2020 guideline, `kind=guideline`): permitted under rule 4 as the source for the maneuver's use, but B attached no estimate to it and the record is marked quantified — rule 4 applies to not_quantified records. Keep only if status becomes partially/not_quantified.
- **NUMERIC MISMATCH** (A src[2] Sullivan 1989 `kind=consensus` vs B `kind=primary_study`): CIWA-Ar validation paper; primary_study is right.
- **DIRECTION — threshold**: CAGE ≥2 is a score threshold, not a history item; card must not present 0.87 as "sensitivity of asking about alcohol use".

---

## Skin / neuro / respiratory muscle

### exam_cellulitis_unilateral_warmth_border
- **VERIFIED**: Pulia 2024 "ALT-70, 22.0% [95% CI, 15.8%–28.1%]" (sensitivity "remained above 90%"); Raff 2017 "79 (30.5%) of 259 patients were misdiagnosed".
- **SCOPE — composite ≠ discriminator** (A est[0], B est[0]): ALT-70 is a 4-item score; the record's finding is the asymmetry item. Both disclose. Spec 0.22 for the score at its rule-out threshold will read as "unilateral erythema is 22% specific" on the card — actively misleading without the composite label.
- **STATUS** (B est[1]): all-null estimate carrying only a misdiagnosis rate; `prevalence=0.695` is 1 − misdiagnosis rate *among patients already labelled cellulitis* — that is a PPV of the admitting diagnosis, not a prevalence. Null it; keep in notes.
- **NO LOCATION** (A+B est[0] `sensitivity=null`): abstract says ">90%"; both correctly refused to enter a number. Good.
- Both partially_quantified; both honest that the isolated finding has no accuracy study. Consider not_quantified.

### exam_ascending_symmetric_weakness_areflexia
- **VERIFIED**: Fokke 2014 "Decreased reflexes in paretic arms or legs were found initially in 91% of patients and in all patients during follow-up"; "within 4 weeks in 97%".
- **DIRECTION / definitional sensitivity** (B est[1] `sensitivity=1.0`): "All patients developed bilateral limb weakness" in a cohort *defined* by GBS diagnostic criteria that require bilateral weakness — sens = 1.0 is tautological (incorporation). Null or label "case-definition feature".
- **SCOPE** (A est[1]): "nadir within 4 weeks 97%" is a time-course feature, not the exam finding.
- **POPULATION COLLAPSE — no comparator** (A+B): case-series proportions with no non-GBS group; specificity/LR not estimable; both say so. A `evidence_level=validation_cohort` vs B `single_study` — **NUMERIC MISMATCH**; single_study is right (no external validation of a rule).
- **SECONDARY SOURCE — cleared**: Brighton case definition (Sejvar 2011) as `consensus` is exactly what rule 4 intends.
- Both partially_quantified; arguably not_quantified (no accuracy data at all). Owner rule needed for "sensitivity-only case series".

### exam_fatigable_ptosis_sustained_upgaze
- **VERIFIED**: Mittal 2012 "fatigability on sustained upgaze 0.80/0.63"; Kee 2019 resolves ("73.3% sensitivity and 96.7% specificity" for the upgaze-then-ice-pack test).
- A ≡ B: single estimate, LRs `computed=true` with inputs (2.16 / 0.32), prevalence 101/138 computed, incorporation bias disclosed in both. Rule-compliant.
- **POPULATION COLLAPSE — spectrum/incorporation** (A+B): upgaze fatigability was part of the OMG case definition; sensitivity is inflated. Both disclose. Card must carry the caveat.
- **STATUS** (A+B quantified): one retrospective referral-clinic series with incorporation bias and no CIs; "quantified" is generous. Suggest partially_quantified.
- Title says "60 s"; Mittal's duration is not in the abstract — **DIRECTION — threshold** unevidenced (Kee used 2 min).

### fn_single_breath_count
- **VERIFIED**: Kalita 2020 "At SBC 5 … sensitivity of 90.6% and specificity of 95.2%"; Bhandari 2024 Table 3 (PMC10990392) rows "GBS 19 SBCT>19 had sensitivity of 95% … Kalita et al., 2020", "Myasthenia gravis 25 SBCT < 25 had sensitivity of 80% … Kannan Kanikannan et al., 2014a", "Variety of diseases 21 SBCT of 21 or less had a sensitivity and specificity of 94.4% and 76.62% for VC <20 ml/kg"; Kukulka 2020 "cutoff count of 25 … sensitivity of 80%, and specificity of 60%"; Delmondes 2023 "count lower than 41 … (Sensitivity = 89% and Specificity = 62%)"; Quinn 2021 "SBCpp had 100% sensitivity and 60% specificity".
- **NUMERIC MISMATCH — attribution** (A est[1] vs B est[1]): the ">19, sens 95%" row — A says "68 GBS patients (Kanikannan 2014)"; B says "Kalita 2020 cohort". The review's Table 3 attributes it to **Kalita 2020**. A's population string is not supported by the cited location.
- **NUMERIC MISMATCH — attribution** (A est[3] vs B est[3]): the "≤21, 94.4%/76.62%" row — A attributes to Escossio 2019, B to Bartfield 1994 (hospitalized patients). Delmondes 2023 abstract ("One study of hospitalized patients … count value of 21 for a VC of 20 ml/kg (Sens 94%, Spec 77%)") supports B. A's attribution is probably wrong.
- **NUMERIC MISMATCH** (A est[3] `specificity=0.766` vs B `0.7662`): rounding only.
- **NO LOCATION — review table as source** (A est[1], est[3]; B est[1], est[2], est[3]): five estimates cite the systematic review's Table 3 rather than the primary paper, and the review's own attributions are internally inconsistent (B documents the "<25 / 80%" row being credited to a GBS paper while the text cites Kukulka). Rule 2 says trace to the primary; A did so for the MG row (Kukulka abstract, which adds spec 60%) — A est[2] is the correct version, B est[2] (spec null, attribution "ambiguous") should be replaced by it.
- **DIRECTION — threshold mismatch with title** (A+B): title threshold "<20"; estimates are at 5, 19, 21, 25, 41 with different targets. Both note the "<20" is convention. The card threshold has no direct estimate.
- **POPULATION COLLAPSE** (B est[4], est[5]): dystrophy and ALS clinic populations for FVC thresholds — reasonable as separate rows, but the record's differentials are GBS/MG only; ALS/dystrophy rows are off-differential.
- Both LR computations `computed=true` with inputs. B est[3] LR− 0.073 from a review-table row — fine arithmetically.

---

## Suggested verification order

1. **FABRICATION SUSPECT** — none found. Nothing to do here.
2. **NUMERIC MISMATCH with consequence** (attribution/metadata, not values — all values agree where both packets have them):
   - `fn_single_breath_count` (two rows attributed to different primary studies by A and B; check Bhandari Table 3 + Delmondes; adopt B for ≤21 row, review for >19 row).
   - `hx_neck_pounding_frog_sign` (B `evidence_level=pooled` wrong; fix to single_study; render the 25–1251 CI).
   - `pocus_lv_function_eyeball` (B omits the only pooled estimate; Schick EPSS/MAPSE parenthetical attribution ambiguous; A's LR− = 0.0).
   - `exam_ascending_symmetric_weakness_areflexia`, `hx_alcohol_use_withdrawal_timing`, `hx_pain_abrupt_maximal_onset` (evidence_level / source-kind / year disagreements).
3. **DIRECTION** (highest clinical risk if rendered as-is):
   - `hx_palpitations_before_syncope` A (LR+ 0.74 under a rule-in interpretation).
   - `pocus_pericardial_effusion` B est[2]/[3] (reversed reference standard stored as accuracy).
   - `exam_melena_rectal_exam` est[2] (LR 0.05 in `lr_positive`) and `exam_wheezing` B est[2] (LR+ 0.7) — correct data, renderer risk.
   - Threshold/title mismatches: `exam_tachypnea_rr_gt24`, `exam_calf_asymmetry_gt3cm`, `fn_single_breath_count`, `exam_fatigable_ptosis_sustained_upgaze`, `hx_alcohol_use_withdrawal_timing`.
4. **rce_backed agreements** (A ≡ B, quote verified; fastest to promote): `exam_percussion_dullness`, `exam_egophony`, `exam_melena_rectal_exam`, `hx_neck_pounding_frog_sign` (after evidence_level fix), `exam_pulsatile_abdominal_mass` (A's full strata), `hx_postural_dizziness` (with composite label), `exam_cirrhosis_stigmata` (B's restricted set), `hx_pain_abrupt_maximal_onset`.
5. **POCUS merges** (both packets good, complementary): `pocus_lung_sliding_absent` (B ladder + A eFAST), `pocus_dvt_compression` (A operator split + B protocol split), `pocus_lung_b_lines` (B), `pocus_aaa_aorta_diameter` (B), `pocus_rv_dilation` (either; fix quotes), `pocus_ivc_collapsibility` (B; resolve RAP-threshold sourcing).
6. **Composite/all-null clean-up** (mechanical): drop or relabel composite rows in `hx_vte_risk_factors`, `exam_tachypnea_rr_gt24`, `hx_dizziness_timing_triggers`, `exam_cellulitis_unilateral_warmth_border`, `hx_post_event_confusion` B est[3], ascites ids A est[3]; delete all-null rows in `hx_vte_risk_factors` A, `hx_dizziness_timing_triggers` A, `exam_cellulitis…` B, `pocus_lv_function_eyeball` B.
7. **DECISIONS #21**: fold the two ascites ids (duplication now confirmed by both extractors).
8. **Rest**: the not_quantified pairs (`hx_palpitations_abrupt_onset_offset`, `fn_tap_out_rhythm_regular`) and the two remaining single-source ids.

## Batch verdict

Wave 2 has no fabrication and no unit errors: all 110 quote checks resolved verbatim, including every PMC table row and both Berecki-Gisolf 2×2 reconstructions, and every computed LR in the batch carries `computed=true` with its inputs. The systematic weaknesses are upstream of the numbers. (1) **Composite-for-item substitution**: in 9 ids the extractor, unable to find an item-level estimate, entered a score or "any abnormal X" composite (Wells score, ALT-70, "any abnormal vital sign", Calgary score, Herr triad, "dizziness OR pulse ≥30", overall clinical impression) as if it quantified the titled finding; the prompt must say a composite may be entered only with a `COMPOSITE:` prefix in `target_condition`, and it never upgrades `evidence_status`. (2) **Threshold drift**: five titles fix a threshold (RR >24, calf >3 cm, SBC <20, upgaze 60 s, CAGE) that no cited estimate uses; the prompt should require the estimate's threshold to be stated in a dedicated field and mismatches with the title to force `partially_quantified`. (3) **All-null "estimates"**: four packets used `estimates[]` rows to preserve a quote for reliability, kappa, prevalence or misdiagnosis figures; rule 1 already forbids this — restate it as "an estimates[] row must carry at least one of sens/spec/LR". (4) **Systematic-review tables as terminal sources**: when a review's Table N is the only accessible location, extractor-A and B attributed the same rows to different primary papers; require the primary PMID in `population` or a `via_review=true` marker, and prefer the primary abstract whenever it is on PubMed (A did this for Kukulka and got a specificity B lacked). (5) **Direction consistency**: one packet's only estimate (LR+ 0.74) contradicts its own `positive_finding` text; add a self-check line — "does any estimate with LR+ < 1 or LR− > 1 agree with `interpretation`?" (6) **Status inflation for LR-only rows**: `quantified` was applied to records with no sens/spec, no CI, and one direction; define `quantified` as "≥1 estimate with both directions or a full 2×2 from a source the verifier can open". (7) The 25-word quote cap is silently dropping CIs (three cases); allow 35 words when the CI would otherwise be cut. Extractor-B is more faithful to spec (splits directions, refuses unevidenced prevalence, labels composites) but under-searches OA full text (missed Berecki-Gisolf twice, Albaroudi once); extractor-A finds more but over-asserts (reference standards, prevalences, attributions, status).

## Category counts (flags, both packets, this file)

| Category | Count | Notes |
|---|---|---|
| FABRICATION SUSPECT | 0 | 110/110 quotes found |
| NUMERIC MISMATCH | 13 | all metadata/attribution/labels; no A-vs-B value conflict on a shared estimate |
| NO LOCATION | 15 | mostly unevidenced prevalence, CI dropped by word cap, stitched quote (1), review-table attribution (5) |
| SECONDARY SOURCE | 2 | TiTrATE narrative review as `consensus` (A and B) |
| SILENT COMPUTATION | 0 new; 6 diff_report flags **cleared** as source-printed LRs | Arts ×2, Fink, Brigo ×2, Albaroudi, Airapetian |
| POPULATION COLLAPSE | 14 | incl. omissions of OA pooled rows (A ×2, B ×2) and naive literature-pooling (Berecki ×2) |
| VOCAB VIOLATION | 0 | all presentations/differentials/tags in vocab.json |
| SCOPE | 22 | 9 composite-as-item, 8 title-vs-estimate gaps, 3 off-title rows, 2 rule-6 marginal |
| DIRECTION | 12 | 1 estimate-vs-interpretation contradiction, 2 reversed-design/LR-in-wrong-slot, 6 threshold-vs-title, 3 renderer-risk (correct data) |
| UNITS | 0 | no sens/spec > 1; all quote-vs-value gaps are %→proportion or computed LRs |
| STATUS | 11 | 4 all-null estimate rows, 5 over-claimed `quantified`, 2 A/B disagreements resolved in favour of the lower status |
