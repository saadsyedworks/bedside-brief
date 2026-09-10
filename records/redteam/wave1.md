# Red-team review — wave 1 (24 ids, 48 packets)

Reviewer: red-team subagent, 2026-09-10. Scope: extends `records/diff_report.md` (mechanical) with judgment.
Method: every packet read; per id ≥2 consequential estimates checked with `python3 tools/pubmed.py fetch|grep|fulltext`
(title, authors, quote-in-abstract; PMC full text for Table-located quotes: PMID 31110214, 37377515, 24223233, 26464292).
Categories: NUMERIC MISMATCH · NO LOCATION · SECONDARY SOURCE · SILENT COMPUTATION · POPULATION COLLAPSE · VOCAB VIOLATION · SCOPE · FABRICATION SUSPECT · DIRECTION · UNITS.
"VERIFIED" lines record what resolved cleanly so the owner need not repeat the lookup.

Batch-wide results first:
- **UNITS**: no sens/spec/prevalence > 1 in any packet; every percent-quote matches its stored proportion. Clean.
- **SECONDARY SOURCE**: no guideline/consensus/textbook source backs any numeric estimate. Clean.
- **NO LOCATION**: every numeric estimate carries a quote + location; all abstract quotes checked were found verbatim (see per-id). Residual issues are spliced quotes and "empty" estimates, flagged below.
- **SILENT COMPUTATION (mechanical false positives)**: the diff report's `LR+ equals sens/(1-spec) but computed=false` hits on `exam_pulse_irregularly_irregular` (A/B est[0],[1]), `exam_murmur_late_peaking_systolic` (A est[1], B est[3]), `exam_pulsus_paradoxus` (B est[2]) — plus `exam_carotid_upstroke_delayed` A/B est[0] and `exam_pulmonary_crackles` A est[0] — are NOT silent: the LR is printed in the source (Cooke/Taggar abstracts; Shellenberger Table 2; Wright 1996 abstract; Htun Table 2). No true silent computation found in wave 1; every derived LR has `computed=true` + `computed_from`.

---

## exam_jvp_elevated
- VERIFIED: Butman PMID 8409071 quote (81%/80%) in abstract [A est0, B est0]; Renier PMID 29252938 "(0.88, pooled odds ratio: 7)" [B est1]; Mant PMID 19586584 "elevated jugular venous pressure (70%)" [B est2].
- **POPULATION COLLAPSE** (A est[0], B est[0]): the only estimate in A is the Butman composite "JVD at rest OR inducible by abdominal pressure" in 52 transplant candidates — not resting JVP; same numbers are also entered as `exam_abdominojugular_reflux` B est[0] (one composite credited to two discriminators).
- **SCOPE** (B est[1].specificity, est[1].location "Abstract, Conclusion"): the sentence "(0.88, pooled odds ratio: 7)" does not name the statistic; "specificity" is an inference (consistent with the abstract's "pooled specificity … 0.69–0.88", but label it inferred).
- **FABRICATION SUSPECT** (B sources[5]): Mueller 2005 cited as "Mueller C, Frana B, Scholer A…"; PMID 16239975 resolves to Mueller C, Frana B, **Rodriguez D**, Laule-Kilian K, Perruchoud AP. Citation error, number not affected.
- NO LOCATION-lite (B extraction_notes): "Wang 2005 reports JVD LR+ ~5.1 in its evidence table" recorded without having viewed the table. Not an estimate, but an unlocated number in the record.

## exam_abdominojugular_reflux
- VERIFIED: Sochowski PMID 2220606 both quotes + kappa 0.74 [A est0/1]; Ducas PMID 6650420 "16 of 19" [B est1]; Butman [B est0].
- **NUMERIC MISMATCH**: A and B share no estimate (A: Sochowski RAP/RVEDP; B: Butman composite + Ducas). Owner must choose the anchor.
- **SCOPE** (A est[0], est[1]): threshold = sustained rise ≥1 cm in 65 patients "free of heart failure"; targets are RAP >9 / RVEDP >12 mmHg, not HF — title says >3 cm rise. A discloses; the numbers should not be rendered as AJR-for-HF accuracy.
- **POPULATION COLLAPSE** (B est[0]): duplicate of the JVP record's composite (see above).
- **FABRICATION SUSPECT** (B sources[5]): Mueller author-list error (as above).
- Note: B est[1] "specificity not computable" — correct handling; B est[1].reference_standard ("impaired cardiac function classified clinically/hemodynamically") is vague but honest.

## exam_s3_gallop
- VERIFIED: Wang PMID 16234501 "positive LR = 11; 95% CI, 4.9-25.0" [A/B est0]; Martindale PMID 26910112 "4.0 … 2.7 to 5.9" [A/B est1]; Marcus PMID 15886379 "41%, 52%, and 32%" / "92%, 87%, and 92%" [B est2/3]; Fonseca PMID 15542419 "ventricular gallop (LR 30.0)" [A est2]; Mant/Renier quotes [B est4/5].
- rce_backed agreement: est[0] (Wang LR+ 11) and est[1] (Martindale 4.0) identical A/B.
- **SCOPE** (B est[2], est[3]): Marcus S3 detected by computerized phonocardiography, not auscultation; disclosed, but bedside applicability is not established.
- **POPULATION COLLAPSE** (B est[4]): Mant "added heart sounds" (S3 and/or S4) entered as S3; LR+ 11 computed from specificity rounded to 99% (B admits "numerically unstable"). Recommend null LR.
- **SCOPE** (B est[5]): Renier "(0.97)" statistic unnamed in the sentence; inferred specificity.
- NUMERIC MISMATCH (status): A partially_quantified vs B quantified on the same anchor numbers — status rule ambiguity, not evidence disagreement.

## exam_pulmonary_crackles
- VERIFIED: Htun PMID 31110214 Table 2 row "Crackles 6 3,671 0.39 (0.28–0.51) 0.83 (0.65–0.92) 2.42 (1.19–4.69) 0.75 (0.61–0.91)" found in PMC full text [A est0]; abstract "crackles (2.42; 1.19-4.69)" [B est3]; Wang "rales (negative LR = 0.51 …)" [A est1/B est0]; Renier "rales (pooled NLR=0.35)" + "(0.77 …)" [B est1]; Marchello PMID 30850460 "LR- of 0.10 (0.07 to 0.13)" [B est4]; Fonseca 23.3 [A est2].
- rce_backed agreement: Wang rales LR- 0.51 identical A/B.
- **POPULATION COLLAPSE** (B est[3]): B left Htun sens/spec null claiming "PMC full text truncated at ~20 kB"; the tool returns 48 kB and Table 2 is present (A used it). B's own population line ("13 studies, 11,144 participants; prevalence 5–50%") was verified in that full text — the omission is a tool-use error, not a data limit.
- **SCOPE** (B est[4]): Marchello LR- 0.10 is a composite (normal vitals AND normal lung exam) — disclosed in target_condition, but it is not the crackles sign and will render under this record.
- **SCOPE** (B est[1]): specificity 0.77 and NLR 0.35 come from different abstract sentences/analyses; "0.77" statistic unnamed.
- SCOPE (both): title's bibasilar-vs-focal discrimination has no quantitative source; both disclose (fine).

## hx_orthopnea
- VERIFIED: Fonseca "orthopnea (LR 39.1)" [A est0]; Ekundayo PMID 19576357 "52% (… 46% to 58%), 83% (… 82% to 84%)" [A est1]; Mant "orthopnoea (89%)" [B est0].
- **NUMERIC MISMATCH**: no shared estimate; B has specificity only.
- **POPULATION COLLAPSE** (A est[1]): Ekundayo is the composite "orthopnea OR PND" in a community prevalence cohort (CHS), not dyspneic patients; the identical row is reused in `hx_pnd` A est[2].
- **SCOPE** (A est[0]): Fonseca LR 39.1, no CI, screening design, sensitivity <36% — `interpretation_label: rule_in` overstates a single-study number.
- **FABRICATION SUSPECT** (B sources[3]): Mueller author-list error.
- NO LOCATION-lite (B extraction_notes): "Wang RCE orthopnea LR+ ~2.2 (CI ~1.2–3.9) in its evidence table" — number recorded from memory, table not viewed.

## hx_pnd
- VERIFIED: Wang "paroxysmal nocturnal dyspnea (positive LR = 2.6; 95% CI, 1.5-4.5)" [A/B est0]; Fonseca 35.5 [A est1]; Ekundayo [A est2].
- rce_backed agreement: est[0] identical A/B.
- **POPULATION COLLAPSE** (A est[2]): composite orthopnea-OR-PND (see hx_orthopnea).
- SCOPE (A est[1]): Fonseca 35.5 no CI, `rule_in` label on a screening-cohort single study.
- NUMERIC MISMATCH (status): A partially vs B quantified with identical anchor evidence.
- **FABRICATION SUSPECT** (B sources[2]): Mueller author-list error.

## exam_peripheral_edema_pitting
- VERIFIED: Mant abstract — "oedema (72%)" is in the specificity list and "53% (oedema)" in the sensitivity sentence [A est0]; Renier ranges "peripheral edema (0.29-0.77)" / "(0.67-0.89)" [B est0].
- **NUMERIC MISMATCH**: A enters Mant sens 0.53/spec 0.72 (+computed LRs); B enters an estimate with every numeric field null.
- **NO LOCATION** (B est[0]): an "empty" estimate (ranges only in the quote) violates spec rule 1 (no number → no estimate; explain in notes). Also B's quote and A's quote are both spliced with "…" from two sentences, i.e., not one verbatim ≤25-word span.
- SCOPE (both): pitting/non-pitting/unilateral distinctions unquantified — both disclose.
- Minor: A setting "mixed" for a primary-care IPD meta-analysis.

## exam_orthostatic_vitals
- VERIFIED: McGee PMID 10086438 "97% (95% CI, 91%-100%)", "22% (… 6%-48%)", "specificity is 98% (… 97%-99%)", "sensitivity, 33%; 95% CI, 21%-47%"; abstract confirms the composite ("severe postural dizziness … or a postural pulse increment of 30 beats/min or more").
- rce_backed agreement: est[0] and est[1] identical A/B (values, CIs, computed LRs).
- **SCOPE** (both): the title's SBP ≥20 / DBP ≥10 mmHg criterion is unquantified (both disclose); all estimates are healthy-volunteer phlebotomy models labelled `evidence_level: pooled`.
- **SCOPE** (B est[2]): "supine hypotension" is a comparator finding, not this maneuver; should not be an estimate under this record.
- Contraindications present in both (hypotensive/unstable) — good. Minor NUMERIC MISMATCH: setting "mixed" (A) vs "outpatient" (B) for the same volunteer data.

## exam_capillary_refill
- VERIFIED: Schriger PMID 2039096 "6% … 26% … 46%" (13 hypotensive / 19 orthostatic / 47 donors) [A/B est0/1]; Ait-Oufella PMID 24811942 index 2.4 s 82%/73% and knee 4.9 s 82%/84% [A est2, B est2/3]; Jacquet-Lagrèze PMID 38042855 54%/72% [A est3, B est4].
- Agreement: Schriger, Ait-Oufella index, Jacquet-Lagrèze rows identical A/B; B adds the knee-CRT row.
- **SCOPE** (both): 3 of 4–5 estimates are PROGNOSTIC (14-day / in-hospital death), not diagnostic; target_condition says so, but `interpretation_label`/`evidence_level` treat them as diagnostic accuracy for a sign titled as a diagnostic threshold. Consider `evidence_status: partially_quantified` for the diagnostic question or a "prognostic" marker.
- **SCOPE** (both est[0], est[1]): reference standard is circular (hypotension / abnormal orthostatics define "hypovolemia"), n = 13 and 19.
- No SILENT COMPUTATION: all LRs computed=true with inputs.

## fn_passive_leg_raise
- VERIFIED: Monnet PMID 26825952 "0.85 (0.81-0.88) … 0.91 (0.88-0.93)", "0.56 (0.49-0.53)", "0.83 (0.77-0.88)" [A/B est0/1]; Cherpanath PMID 26741579 "86% (95% CI, 79-92) … 92% (88-96)" [A est2], "85% [78-90] … 92% [87-94]" [B est2], "58% [44-70] … 83% [68-92]" [A/B est3].
- Agreement: Monnet CO and PP rows identical A/B (including the flagged typographic CI).
- **NUMERIC MISMATCH** (A est[2] vs B est[2]): A = Cherpanath overall pooled (86/92), B = flow-variable subgroup (85/92). Both verified; they are different subgroups, not an error — owner picks one and labels it. B computes LR+ 10.6 from its row; A leaves LR null.
- **SCOPE** (A safety_scope): no `skill_assumption` although the VTI readout is POCUS-dependent; B provides one. Contraindications (raised ICP, IAH, fractures) present in both — good.
- Minor: setting "ICU" (A) vs "mixed" (B) for Cherpanath (ICU/OR/ED).

## exam_pulsus_paradoxus
- VERIFIED: Roy PMID 17456823 "pooled sensitivity, 82%; 95% CI, 72%-92%", "3.3; 95% CI, 1.8-6.3", "0.03; 95% CI, 0.01-0.24"; abstract confirms "Based on 1 study" and 8 included studies. Wright 1996 PMID 8790120 "sensitivity was 0.42, the specificity was 0.89, and the likelihood ratio was 3.86" [B est2] — authors are Wright RO, Steele DW, Santucci KA (B left the author list blank; fill, not fabricated).
- rce_backed agreement: both Roy estimates identical A/B.
- SILENT COMPUTATION: diff-report hit on B est[2] is a false positive (LR 3.86 is printed).
- **SCOPE** (B est[2]): pediatric ED, continuous non-invasive measurement, threshold >15 mmHg at 30 min, outcome = admission/relapse — not the manual-cuff >10–12 mmHg sign in adults; disclosed but should not render as this record's asthma accuracy.
- **VOCAB VIOLATION (soft)** (both clinical_mapping.differentials): `constrictive_pericarditis` is a vocab term but not listed under any of this record's presentations (dyspnea/chest_pain/hypotension; it sits under edema).
- Holleman 1995 (PMID 7815660) and Pearson 1993 have no abstract; cited without numbers — acceptable.

## exam_pulse_irregularly_irregular
- VERIFIED: Cooke PMID 16451780 94% (84–97)/72% (69–75), LR+ 3.39, LR- 0.10; Taggar PMID 26464292 0.92 (0.85–0.96)/0.82 (0.76–0.88), PLR 5.2 (3.8–7.2), NLR 0.1 (0.05–0.18).
- Full agreement A/B on both estimates. SILENT COMPUTATION hits (4) are false positives — all four LRs are printed in the abstracts.
- **FABRICATION SUSPECT** (A extraction_notes): "Taggar full text (PMC4952027) reports a sensitivity-analysis pulse-palpation estimate of 0.93 (0.86–0.97)/0.81 (0.76–0.85)". `fulltext 26464292 | grep "0.93 (0.86"` finds nothing; the only "0.93" is BPM specificity 0.93 (0.89–0.96). Unlocated number in notes (not an estimate).
- SCOPE (both): screening/primary-care populations; ED symptomatic performance unknown — disclosed.

## exam_murmur_late_peaking_systolic
- VERIFIED: Shellenberger PMID 37377515 abstract "LR = 10.87 … 3.94-30.12", "LR = 0.11 … 0.06-0.23"; PMC Table 2 rows (diminished S2 0.59/0.95/10.87/0.44; neck radiation 0.93/0.66/2.69/0.11) [A est0/1, B est2/3]; Discussion "LR of 3.7 … (LR = 0.2)" [A est2]; "2 studies, with 216 patients"; kappa 0.33 (neck radiation), 0.54 (S2). Etchells 1997 PMID 9032164 ranges "8.0-101", "0.05-0.10" [B est0/1]; Etchells 1998 PMID 9798818 "LR 0.10; … 0.01, 0.44" [B est4].
- Agreement: diminished-S2 and neck-radiation rows identical A/B. SILENT COMPUTATION hits (A est1 / B est3) are false positives (Table 2 prints 2.69).
- **POPULATION COLLAPSE (range-as-point)** (B est[0].lr_positive = 8.0; B est[1].lr_negative = 0.05): between-study RANGES (8.0–101; 0.05–0.10) entered as point values with `computed=false`; disclosed only in `computed_from`. The renderer will show "LR+ 8.0" as if pooled. Spec rule 1/3 → null with note, or a range field.
- **SCOPE** (A est[2]): narrative aggregate (4 small studies, no CI) from the Discussion labelled `evidence_level: pooled`.
- Minor NUMERIC MISMATCH: source year 2023 (A, print) vs 2024 (B, PubMed) for the same DOI; B citation omits authors.

## exam_carotid_upstroke_delayed
- VERIFIED: Shellenberger abstract "LR = 9.04, 95% CI, 3.12-25.44"; Table 2 row 0.57 (0.37–0.75)/0.94 (0.81–0.98)/9.04/0.46 (0.30–0.71); "6 studies with 815 patients"; Etchells 1997 "2.8-130" [B est1].
- Agreement: est[0] identical A/B. SILENT COMPUTATION hit is a false positive (LR printed).
- **NUMERIC MISMATCH** (safety_scope.interobserver_note): A "kappa 0.33", B "kappa 0.26". Full text: delayed carotid upstroke kappa **0.26**; 0.33 is the kappa for murmur radiation to the neck. A is wrong.
- **POPULATION COLLAPSE (range-as-point)** (B est[1].lr_positive = 2.8): low end of the RCE range 2.8–130 entered as a value.

## fn_murmur_valsalva_standing_louder
- VERIFIED: Lembo PMID 2897627 all four sens/spec pairs (65/96, 95/84, 95/85, 85/75) in abstract.
- Full agreement A/B (values and computed LRs).
- **SCOPE** (B est[*].reference_standard): "Echocardiography/Doppler and catheterization-confirmed etiology … (as described in study)" — the abstract only says "documented systolic murmurs"; B did not access the full text, so the reference standard is asserted, not extracted. A's phrasing is honest.
- SCOPE: 4 estimates from one 50-patient cardiologist series, no CIs, `evidence_status: quantified` — acceptable but note spectrum (HCM vs other murmurs).
- Contraindications (presyncope, instability, fall risk) present in both — good.

## hx_exertional_chest_pain
- VERIFIED: Goodacre PMID 11874776 "exertional pain [LR = 2.35]", "(LR = 2.06)", n=893, 3.8%/9.1%; Chun PMID 15336583 "typical angina (LR=5.8; … 4.2 to 7.8)" [A est2].
- Agreement: Goodacre AMI/ACS rows identical A/B.
- **POPULATION COLLAPSE / SCOPE** (A est[2]): "typical angina" is a 3-feature composite for stable CAD by angiography, not the single feature "exertional pain" in acute chest pain; A also states the reference standard was "inferred … not verifiable". This row drives the status mismatch (A quantified vs B partial).
- NO LOCATION: none. Goodacre LRs have no CI (both disclose).

## hx_pain_radiation_both_arms
- VERIFIED: Fanaroff PMID 26547467 "pain radiation to both arms (specificity, 96%; LR, 2.6 [1.8-3.7])"; Panju PMID 9786377 "(LR, 7.1)"; Goodacre "(LR = 4.07)"; Bruyninckx PMID 18307844 "Sweating … 2.92 (1.97 to 4.23)".
- rce_backed agreement: all four estimates identical A/B.
- **SCOPE** (both est[3]; A interpretation.positive_finding): sweating pooled over "non-selected patients (primary care and ED)", while Goodacre's abstract states "nausea, vomiting, or diaphoresis were not predictive of AMI or ACS" (verified). B notes the heterogeneity; A's positive_finding presents LR+ 2.9 without it.
- SCOPE (both est[2]): Goodacre "shoulder or both arms" ≠ both arms — disclosed.
- NUMERIC MISMATCH (status): identical estimates, A quantified vs B partially_quantified.

## exam_chest_wall_tenderness_reproducible
- VERIFIED: Bruyninckx "Absence of chest-wall tenderness … LR- of 0.23 (0.18 to 0.29)", sens 92% (86–96) AMI / 94% (91–96) ACS; Chun "chest wall tenderness (LR=0.3; 0.2 to 0.4)" [A est1]; Goodacre "(LR = 0.3)"; Panju "(LR range, 0.2-0.4)" [B est2].
- **DIRECTION (handled, verify)** (A est[0], B est[0]): source reports the inverted sign (absence, LR- 0.23); both re-label it as LR of tenderness-present = 0.23 in `lr_positive` with `computed=true`. Arithmetically correct; owner should confirm the field convention (lr_positive = LR when finding present).
- **SCOPE** (B est[0].target_condition = "Acute myocardial infarction"): the abstract does not say whether LR- 0.23 is for AMI or ACS (A flags this ambiguity); B assigns AMI without evidence. B's sensitivity 0.08 (0.04–0.14) is 1−0.92 with CI ends swapped — fine as computed.
- **POPULATION COLLAPSE (range-as-point)** (B est[2].lr_positive = 0.2): Panju range 0.2–0.4 entered at its most favourable end.
- NUMERIC MISMATCH: A carries Chun 0.3 (0.2–0.4), B does not; B carries Panju 0.2, A does not.

## hx_pleuritic_chest_pain
- VERIFIED: Panju "pleuritic chest pain (LR, 0.2)"; Swap PMID 16304077 "stabbing, pleuritic, positional, or reproducible by palpation (LRs 0.2-0.3)"; Courtney PMID 20045580 "pleuritic chest pain (OR 1.53)".
- **DIRECTION** (B est[0]): the LR 0.2 applies to pleuritic pain PRESENT (lowers MI); B stores it in `lr_negative` (= finding absent). A stores it in `lr_positive`. As stored, B would render "absence of pleuritic pain lowers MI probability". Most serious single-field error in the batch.
- **NO LOCATION / empty estimate** (A est[1], est[2]): entries with every numeric field null, kept "for the quote only" (Swap range; Courtney OR). Spec rule 1 says null the estimate and explain in notes, not create an estimate.
- NUMERIC MISMATCH (status): A partially vs B quantified on one identical number.
- SCOPE (both): PE direction unquantified (OR only); both disclose. Pericarditis/pneumonia/pneumothorax unquantified.

## hx_pain_tearing_ripping
- VERIFIED: PMID 29218798 "tearing/ripping pain (specificity = 99.7%, … LR+ = 42.1 [9.9-177.5])"; PubMed authors for 29218798 = **Ohle R, Um J, Anjum O** (case-control); for 29265487 = **Ohle R, Kareemi HK, Wells G** (meta-analysis).
- Agreement: the single estimate is identical A/B.
- **FABRICATION SUSPECT (citation misattribution)** (B sources[0], sources[2]): B attributes the case-control paper to "Ohle R, Kareemi HK, Wells G, Perry JJ" and the meta-analysis to "Ohle R, Um J, Anjum O" — author lists swapped. PMIDs/DOIs resolve correctly, so the number is real; the citations are wrong.
- **UNITS/SCOPE** (A est[0].prevalence = 0.2): 194/(194+776) case-control ratio stored in a prevalence field (A explains in notes; the field will still render/feed Bayes).
- SCOPE (both): "migrating" pain (half the title) unquantified; spectrum bias of matched controls disclosed. A source years 2019 for print-2018 articles (PubMed epub year) — minor.

## exam_pulse_deficit
- VERIFIED: Klompas PMID 11980527 "31% have pulse deficits or blood pressure differentials", "(positive LRs, 5.7 and 6.6-33.0, respectively)", 21 studies; Ohle "pulse deficit (specificity = 99.3, LR+ = 31.1 [11.2-86.6])"; IRAD PMID 10685714 "15.1%".
- rce_backed agreement: Klompas 31%/5.7, Ohle 31.1, IRAD 15.1% identical A/B (A splits Klompas into two rows).
- **POPULATION COLLAPSE** (both, Klompas rows): composite "pulse deficit OR BP differential"; the identical composite estimate is also entered in `exam_bp_differential_arms` (one number credited to two records; disclosed in both).
- **FABRICATION SUSPECT** (B sources[1], sources[3]): Ohle author lists swapped (as in hx_pain_tearing_ripping).
- **UNITS/SCOPE** (A est[2].prevalence = 0.2): case-control ratio as prevalence, not caveated in this packet's notes.
- NO LOCATION-lite (B interobserver_note): "Klompas pooled sensitivity spans 10–40% across studies" — B admits this is "my reading"; not in the abstract. B extraction_notes: meta-analysis abstract "mentions pulse deficit qualitatively" — it says only "hypotension, pulse, or neurologic deficit".

## exam_bp_differential_arms
- VERIFIED: Klompas (as above); PMID 33692296 "L-R >20 mm Hg (14% vs. 4%, p=0.029)", TAAD n=58 vs non-AAD n=122, setting not stated; Um PMID 30021832 "OR 2.7, 95% CI 1.39 to 5.25", "DOR 28.9 … DOR 2.71".
- **FABRICATION SUSPECT** (A sources[1]): cited as "Shibata T, et al." — PMID 33692296 resolves to **Sasamoto N, Akutsu K, Yamamoto T, …** (J Nippon Med Sch 2022). Wrong first author; number verified.
- **FABRICATION SUSPECT** (B sources[2]): Ohle meta-analysis attributed to "Ohle R, Um J, Anjum O" (case-control authors).
- **SILENT COMPUTATION (disclosed, verify)** (A est[2]): sens 0.14, spec 0.96, LR+ 3.5, LR- 0.90 computed from rounded abstract percentages (no counts, no CI); `computed=true` and inputs shown; setting "ED" assumed. Acceptable only if the owner accepts abstract-percentage arithmetic.
- **POPULATION COLLAPSE** (both est[0]): Klompas composite duplicated from the pulse-deficit record.
- NUMERIC MISMATCH: A has a >20 mmHg-specific estimate; B has none (B correctly declined to convert Um's OR). Owner decides whether A's computed row stands.

## hx_syncope_prodrome
- VERIFIED: Albassam PMID 31237649 feeling-cold / headache / mood-change triplets verbatim; Sheldon PMID 16223744 "89% sensitivity and 91% specificity"; Berecki-Gisolf PMID 24223233 PMC Table 2 rows "(Long) prodrome† Yes 46 9 23 21 4 79 - 182 (39%) … 1117 (63%) … 1.66", "Nausea … 34 (8%) … 307 (20%) … 1.15", "Diaphoresis … 86 (18%) … 753 (43%) … 1.42".
- Agreement: Berecki prodrome + nausea rows and Albassam feeling-cold identical A/B (values and computed LRs).
- **POPULATION COLLAPSE / data-integrity** (B est[2] Diaphoresis): in the PMC XML the per-study "Yes" cells sum to 382 (= the printed "No" total) — Yes/No sub-columns are transposed. B used the row totals (86/468 vs 753/1768), which are consistent with the table's LR 1.42; A excluded the row for this reason. Owner should check against the PDF before accepting.
- **SCOPE** (A est[3]): Calgary score is a composite questionnaire, tilt-table reference standard, cohort excludes structural heart disease; prevalence 0.73 is case mix, not prevalence.
- SCOPE (both): situational triggers (micturition, cough, post-prandial) — half the title — unquantified; both disclose.
- DIRECTION check: Albassam LR 0.16 for feeling cold PRESENT correctly in lr_positive; Berecki LR 1.66 for prodrome ABSENT correctly in lr_negative.
- Minor NUMERIC MISMATCH: A source years 2014 (PLoS One 2013) and 2009 (Heart 2008) vs B's print years.

## hx_exertional_syncope
- VERIFIED: Berecki Table 2 "during effort Yes 10 - - 6 - - - 16 (13%) 7 - - 2 - - - 9 (2%) 30.5 1 <0.0001 6.92"; Del Rosso 2005 PMID 16275193 "97%, 99%, and 99%, respectively" (n=261, ≥65 y, 34% cardiac).
- Agreement: est[0] identical A/B (computed LR- 0.89 both).
- **POPULATION COLLAPSE** (both est[0]): raw pooled 2×2 from only 2 Italian cohorts, no CI, labelled `evidence_level: pooled` — both disclose; consider `single_study`-equivalent weighting.
- **VOCAB VIOLATION (soft)** (both differentials): `ventricular_tachycardia` is not a syncope-presentation term in vocab.json (only under palpitations); `tachyarrhythmia` is the syncope term and is already listed.
- SCOPE (B est[1]): specificity-only row (0.99) in ≥65 y — acceptable, sensitivity null.

---

## Suggested verification order (owner)

1. **FABRICATION SUSPECT / citation integrity** — `exam_bp_differential_arms` (A "Shibata" → Sasamoto; B Ohle swap), `hx_pain_tearing_ripping` (B Ohle swap), `exam_pulse_deficit` (B Ohle swap), `exam_pulse_irregularly_irregular` (A unlocated Taggar 0.93/0.81 note), `exam_carotid_upstroke_delayed` (A kappa 0.33 → 0.26), Mueller author error in B ×4 (`exam_jvp_elevated`, `exam_abdominojugular_reflux`, `hx_orthopnea`, `hx_pnd`).
2. **DIRECTION + NUMERIC MISMATCH** — `hx_pleuritic_chest_pain` (B lr_negative), range-as-point values in B (`exam_murmur_late_peaking_systolic` est0/1, `exam_carotid_upstroke_delayed` est1, `exam_chest_wall_tenderness_reproducible` est2), `fn_passive_leg_raise` (Cherpanath overall vs flow subgroup), `exam_peripheral_edema_pitting` (A numbers vs B empty), no-overlap pairs (`exam_abdominojugular_reflux`, `hx_orthopnea`), status-only mismatches (`exam_s3_gallop`, `hx_pnd`, `hx_exertional_chest_pain`, `hx_pain_radiation_both_arms`, `hx_pleuritic_chest_pain`).
3. **rce_backed agreements (quotes verified, ready to promote)** — `hx_pnd` est0 (Wang 2.6); `exam_s3_gallop` est0/1 (Wang 11, Martindale 4.0); `exam_pulmonary_crackles` Wang rales 0.51; `exam_pulsus_paradoxus` both Roy rows; `exam_orthostatic_vitals` both McGee rows; `hx_pain_radiation_both_arms` all four; `exam_chest_wall_tenderness_reproducible` Bruyninckx relabel; `hx_syncope_prodrome` Albassam feeling-cold; `exam_pulse_deficit` Klompas composite; `exam_murmur_late_peaking_systolic` / `exam_carotid_upstroke_delayed` Shellenberger Table 2 rows (pooled MA, not RCE).
4. **The rest (SCOPE / composite / prognostic)** — composite duplicates (Butman, Klompas, Ekundayo, Chun typical angina, Mant added heart sounds, Marchello, Calgary), `exam_capillary_refill` prognostic rows, `fn_murmur_valsalva_standing_louder` reference standard, `hx_exertional_syncope` 2-cohort pool, VOCAB cross-presentation differentials, source-year quirks.

## Batch verdict (for the extractor prompt before wave 3)

Numbers are honest: 100% of sampled quotes (≈95 phrases across 45 PMIDs) were found verbatim, no percent/proportion or >1 errors, and every derived LR carries `computed=true` with inputs — the diff report's SILENT COMPUTATION hits are all false positives where the LR is printed in the source. The systematic weaknesses are structural, not numeric: (1) **composites entered as single signs and the same composite reused across two records** (JVP+AJR, pulse-deficit+BP-differential, orthopnea+PND, "typical angina", "added heart sounds", Marchello rule-out, Calgary score); (2) **between-study ranges collapsed to a point value** with `computed=false` (extractor-B, four rows) — the renderer cannot tell "8.0" from a pooled LR; (3) **citation author lists typed from memory** (Ohle swap ×3 packets, "Shibata", Mueller ×4) while PMIDs are correct — add a validator that compares `sources[].citation` first author/year to `pubmed.py fetch`; (4) **field-direction ambiguity**: one packet stored a finding-present LR in `lr_negative`; the prompt must define `lr_positive` = LR when finding present, `lr_negative` = LR when absent, and require an explicit relabel note when the source reports the inverted sign; (5) **`evidence_status` rule is undefined** — 6/24 status mismatches arise on identical evidence; (6) **empty estimates** (all-null numeric fields "for the quote") and **case-control ratios in `prevalence`** should be forbidden; (7) numbers recalled from unviewed tables (Wang JVD 5.1, AJR 6.4, orthopnea 2.2, S3 LR- 0.88, rales LR+ 2.8, Swap 4.7, Taggar 0.93) appear in `extraction_notes`/`interobserver_note` without location — either ban them or tag "unverified recall"; and `interobserver_note` statistics (kappa) need the same quote+location discipline as estimates. Tool hygiene: instruct extractors that `pubmed.py fulltext` returns up to 200 kB (one extractor believed 20 kB and skipped an available Table 2), to copy author lists from `fetch` output, and to flag prognostic outcomes separately from diagnostic accuracy.
