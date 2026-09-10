# Phase 0 owner gate — Bedside Brief

Generated at commit `4ca7c62`. Everything below is a DRAFT until you sign off; after sign-off I commit **freeze #1** and write its hash into every case file.

## What you are approving

- `discriminator_ids.json`: **148 ids** — {'exam': 80, 'functional': 15, 'history': 39, 'pocus': 14}; evidence expectation {'rce_backed': 77, 'likely_not_quantified': 24, 'likely_quantified': 47}; priority {1: 93, 2: 50, 3: 5}. Every `anchor_source` PMID was confirmed against PubMed by title.
- `benchmark/cases/`: **36 base cases = 108 inputs** (each file nests one perturbation pair + one noise variant), 204 free-text targets (101 must-have), 3 deliberately underspecified cases (ams_003, dizziness_003, weakness_003). Two critic passes + one re-check applied; `python3 tools/validate.py cases` = 0 errors.
- `vocab.json`: **unchanged**. Wish-list from the drafters is listed under decision 2.

Ids per presentation (an id can serve several): dyspnea 58, chest_pain 46, syncope 39, palpitations 14, edema 28, hypotension 46, aki 40, dizziness 28, ams 33, abdominal_pain 33, fever 46, weakness 29

## Decisions I need from you (numbered; reply with the number and your call)

1. **Approve the 148-id list as the extraction universe**, or name ids to drop/add/rename. Cardiology + volume are deep on purpose (dyspnea 60, hypotension 48, chest pain 48, syncope 41, AKI 40); palpitations is thin (14) — say if you want 5–8 more there (e.g. exertional palpitations, thyroid exam, anxiety features).
2. **Vocab: keep frozen as-is (my recommendation) or add terms now.** Differentials the id drafters wanted but that are NOT in vocab.json (none was needed by a benchmark case): `bacteremia`, `upper_gi_bleed`, `spinal_epidural_abscess`, `hypothyroidism` (myxedema edema), `aortic_regurgitation`, `mitral_regurgitation`, `tension_pneumothorax`, `alcohol_withdrawal` / `opioid_toxicity` (vs one `intoxication_withdrawal`), `delirium_metabolic` (only `delirium_infectious` exists — CAM maps awkwardly), `intracranial_hemorrhage`, `vestibular_migraine`, `neurogenic_shock`, `hypercalcemia`, `incarcerated_hernia`, `ectopic_pregnancy`/`ovarian_torsion`, `seizure_todd_paresis`, `transverse_myelitis`. Cross-listing gaps (term exists but not under the presentation where retrieval needs it): `aortic_dissection` not under hypotension; `anxiety_hyperventilation` not under palpitations; `hyperthyroidism` not under edema/syncope; `pericarditis` not under dyspnea/fever; `pulmonary_embolism` not under edema; `urinary_retention` not under aki (drafters used `obstruction_retention`). Indication tags wanted: `urinary_catheter`, `central_line`, `recent_antibiotics`, `nsaid_use`, `chronic_steroids`, `opioid_use`, `benzodiazepine_use`, `recent_contrast`, `prosthetic_joint`, `neutropenic`, `smoker`, `hemoptysis`, `known_cad`, `known_valve_disease`, `family_hx_sudden_death`, `bph_known`, `hearing_loss`. Recommendation: add NOTHING before freeze #1 (every case and id validates today); revisit after Phase 3 library-coverage numbers show which gaps cost recall.
3. **must_have on guideline-only maneuvers (DECISIONS #14).** 31 of 101 must-have targets (≈31%) will map to `not_quantified` (guideline-only) records per the critic re-check (e.g. medication review in syncope_002, source exam in hypotension_001, hemodynamic-stability check in palpitations_002). Keep them as must-have (recall counts them, and not-quantified is first-class), or demote all to should-include so must-have recall is purely literature-backed?
4. **Off-bedside boundary (DECISIONS #11).** I classified medication/MAR review as bedside history and SpO2, telemetry, I/Os, weights, POC glucose, bladder scan as off-bedside. Confirm, or move MAR review to off-bedside (this changes ~15 targets and the eval classifier).
5. **Compound targets (DECISIONS #13).** A target like "Neck stiffness, Kernig, Brudzinski, jolt accentuation" counts as present if ANY component is on the card. Confirm, or require ALL components.
6. **POCUS stays extracted-but-disabled** (14 pocus ids will be extracted; never retrieved until you flip DAY1_FREEZE.md). Confirm.
7. **Branch redundancy:** dyspnea_003, chest_pain_002 and edema_003 are all VTE-branch cases in different presentations. Critic says acceptable; author declined to re-branch chest_pain_002 to pneumothorax. Keep, or re-branch chest_pain_002?
8. **Sign-off wording:** reply "freeze #1" (optionally with edits) and I commit, hash-stamp all 36 files, and mark the benchmark read-only.

## The 6 sample cases (one per pair of presentations)

### dyspnea_001  (dyspnea; dx: acute_decompensated_hf, pneumonia, pulmonary_embolism)
**Input:** 68M HFrEF EF 30%, admitted for cellulitis, got 3L IVF yesterday, now short of breath overnight, sat 89% on room air

- **MUST** — JVP (jugular venous pressure) at 45 degrees, elevated  
  _Elevated JVP is the strongest bedside sign of elevated filling pressures_
- **MUST** — S3 gallop (third heart sound) at the apex in left lateral decubitus  
  _S3 is highly specific for decompensated heart failure_
- **MUST** — Ask about orthopnea and paroxysmal nocturnal dyspnea since the fluid bolus  
  _Orthopnea/PND point to elevated left-sided filling pressures_
- should — Abdominojugular reflux  
  _Positive reflux supports elevated right atrial pressure_
- should — Bibasilar crackles and wheeze on lung auscultation  
  _Crackles support pulmonary edema; wheeze may be cardiac asthma_
- should — Check for new bilateral pitting edema (and sacral edema)  
  _Fluid retention after 3L supports volume overload_

- Off-bedside OK: BNP; chest x-ray; ECG; troponin; basic metabolic panel; daily weight trend
- Should NOT: Empiric IV diuresis before volume examination (JVP, S3 gallop, crackles); Continuing maintenance IV fluids for the cellulitis without a volume examination; Rely on chest x-ray alone to decide fluid status
- Underspecified flag: False
- **Perturbation** (added fever (38.9 C)): 68M HFrEF EF 30%, admitted for cellulitis, got 3L IVF yesterday, febrile to 38.9 tonight, now short of breath overnight, sat 89% on room air  
  → Focal consolidation exam (egophony, bronchial breath sounds, dullness; Focal crackles) becomes must_have and ask about cough/sputum/rigors rises; JVP and S3 gallop remain must_have; edema check drops to should-still-include.
- **Noise:** Sixty-eight year old gentleman, retired mechanic, room 427, known heart failure with EF around 30 percent, in for leg cellulitis, received three liters of IV fluid yesterday, wife reports he is breathless tonight, saturation 89 percent on room air  
  → None. Card should be substantially identical to base.

### syncope_002  (syncope; dx: tachyarrhythmia, bradyarrhythmia, orthostatic_hypotension, seizure_mimic)
**Input:** 81F on sotalol for AF, found on floor by bed, no memory of event, no prodrome, tele leads off at the time, K 3.1 this AM

- **MUST** — Ask about prodrome (none vs palpitations vs lightheadedness), what she was doing (lying vs standing), and duration of unconsciousness  
  _Absent prodrome and supine onset favor arrhythmia_
- **MUST** — Witness account: duration, color, jerking, tongue biting, incontinence, post-event confusion (from nurse)  
  _Separates arrhythmic syncope from seizure_
- **MUST** — Medication review (MAR): sotalol dose and timing, other QT-prolonging or AV-nodal agents, recent additions  
  _Sotalol with hypokalemia is a torsades set-up; AV-nodal agents cause bradyarrhythmia; indispensable here, likely maps to a not_quantified record_
- should — Orthostatic vital signs (supine to standing at 1 and 3 min)  
  _Excludes an orthostatic contribution in an elderly inpatient_
- should — Examine for injury (head, hip) and perform a cardiac exam for bradycardia, irregular rhythm, or murmur  
  _Injury from unheralded collapse suggests arrhythmia; exam detects rate and structural clues_

- Off-bedside OK: 12-lead ECG with QTc; continuous telemetry; potassium and magnesium; hold sotalol pending review
- Should NOT: Carotid sinus massage in a patient on sotalol with suspected conduction disease; Attribute to dehydration and remove from telemetry; Tilt-table testing
- Underspecified flag: False
- **Perturbation** (position at onset: found on floor by bed -> collapsed on standing from bed): 81F on sotalol for AF, collapsed on standing from bed, no memory of event, no prodrome, tele leads off at the time, K 3.1 this AM  
  → Orthostatic vital signs (supine to standing at 1 and 3 min) become must_have and orthostatic_hypotension rises; ask about oral intake, diuretics, and days in bed is a new item; prodrome history and Medication review (MAR) remain must_have.
- **Noise:** 81 year old woman, widowed, on sotalol for atrial fibrillation, night nurse found her on the floor beside the bed, cannot recall the event, no warning, telemetry leads were disconnected at the time, potassium 3.1 this morning  
  → None. Card should be substantially identical to base.

### edema_003  (edema; dx: dvt, cellulitis_ssti, pulmonary_embolism)
**Input:** Page: 48F day 4 of pneumonia admission, new right calf swelling and pain since this afternoon, HR 96, afebrile, SpO2 96%

- **MUST** — Calf circumference asymmetry >3 cm (10 cm below tibial tuberosity)  
  _Objective asymmetry is the most reproducible Wells criterion for DVT_
- **MUST** — Wells DVT items on history and exam: bedridden >3 days, active cancer, prior VTE, recent surgery, pitting edema confined to the symptomatic leg, collateral superficial veins  
  _Structured pretest probability determines whether ultrasound can wait until morning_
- should — Ask about pleuritic chest pain, dyspnea, or presyncope; check resting heart rate and respiratory rate  
  _Screens for concurrent pulmonary embolism, which changes urgency_
- should — Inspect for well-demarcated erythema, warmth, lymphangitic streaking, and a portal of entry  
  _Cellulitis is the main mimic of DVT in a unilateral swollen leg_
- should — Palpate along the deep venous course for tenderness and a superficial cord; note whether edema is pitting and its proximal extent  
  _Localizes the process and estimates proximal extension_

- Off-bedside OK: Compression ultrasound of the leg; D-dimer (limited value in an inpatient); CBC; checking whether pharmacologic VTE prophylaxis was ordered and given
- Should NOT: Homan's sign as a rule-in or rule-out test; Empiric therapeutic anticoagulation without examining the leg or estimating pretest probability; Withholding the leg examination because an ultrasound is ordered for the morning
- Underspecified flag: False
- **Perturbation** (unilateral right calf swelling and pain -> bilateral symmetric leg swelling and aching (single swap: laterality)): Page: 48F day 4 of pneumonia admission, new bilateral symmetric leg swelling and aching since this afternoon, HR 96, afebrile, SpO2 96%  
  → DVT falls: Calf circumference asymmetry >3 cm and Wells items drop; JVP with Abdominojugular reflux and Medication review (MAR) for cumulative IV fluids, dihydropyridine, and steroids rise to must_have; cellulitis inspection drops.
- **Noise:** Forty-eight-year-old woman in 7-West bed 3 (nurse Maria calling), admitted four days ago with pneumonia; since this afternoon her right calf is swollen and sore; heart rate 96, no fever, saturating 96%  
  → None. Card should be substantially identical to base.

### hypotension_002  (hypotension; dx: hypovolemic_hemorrhagic_shock, septic_shock, medication_effect, atrial_fibrillation_flutter)
**Input:** Cross-cover: 63M on apixaban for AF, admitted with CAP, day 2, BP 88/54, HR 118, pale and lightheaded when he stood to void

- **MUST** — Ask about melena, hematemesis, and hematochezia; Digital rectal examination (DRE) for melena  
  _Occult GI bleeding on an anticoagulant is the leading cause; melena on rectal exam has a very high LR for severe upper GI bleeding_
- should — Orthostatic vital signs (supine to standing at 1 and 3 min) (postural pulse increment >=30/min), only if supine SBP >=90  
  _Postural pulse increment is the most accurate bedside sign of large-volume blood loss, but supine hypotension already meets the criterion and standing is unsafe below SBP 90_
- **MUST** — Conjunctival pallor, Capillary refill time, skin temperature, and pulse regularity (rapid AF versus sinus tachycardia)  
  _Conjunctival rim pallor has a high LR+ for anemia; perfusion and pulse regularity separate blood loss from a primary rate problem_
- **MUST** — Ask about prior upper GI bleeding, NSAID or aspirin use, cirrhosis or known varices, and alcohol  
  _A history of prior upper GI bleeding carries a high LR for a severe bleed and directs urgency of endoscopy_
- should — Examine the abdomen for tenderness and the flanks and thighs for hematoma  
  _Identifies retroperitoneal or soft-tissue bleeding on an anticoagulant_
- should — Medication review (MAR): antihypertensives, diuretics, and opioids given tonight; temperature and Focal crackles for progression of pneumonia  
  _Medication effect and worsening sepsis are competing explanations_

- Off-bedside OK: CBC and type and screen; ECG; lactate; coagulation studies; GI consult; two large-bore IVs and crossmatch
- Should NOT: Empiric anticoagulant reversal before bleeding is sought on history and exam; Nasogastric lavage to diagnose upper GI bleeding; Standing the patient for orthostatic vital signs while supine SBP remains <90
- Underspecified flag: False
- **Perturbation** (anticoagulant exposure -> loop-diuretic exposure (mechanism of volume loss); AF, admission, vitals kept verbatim): Cross-cover: 63M with AF, not anticoagulated, on IV furosemide BID, admitted with CAP, day 2, BP 88/54, HR 118, pale and lightheaded when he stood to void  
  → Non-hemorrhagic hypovolemia rises: Dry axilla / mucous membranes and asking about oral intake, vomiting, or diarrhea become must_have; the melena question with DRE and the prior-GI-bleed history drop to should-still-include; the conditional Orthostatic vital signs item and conjunctival pallor/Capillary refill time remain.
- **Noise:** 63-year-old man, an accountant, daughter phoned the desk; takes apixaban for atrial fibrillation; second day in with pneumonia; blood pressure 88/54, pulse 118, looks pale and got lightheaded standing up to use the urinal  
  → None. Card should be substantially identical to base.

### abdominal_pain_003  (abdominal_pain; dx: mesenteric_ischemia, perforated_viscus, aaa, small_bowel_obstruction)
**Input:** 79M AF not anticoagulated, sudden severe diffuse abdominal pain 1h, RN says belly soft, HR 118, BP 128/76

- **MUST** — Compare reported pain severity with abdominal tenderness on palpation (pain out of proportion to exam)  
  _Severe pain with a soft, minimally tender abdomen in an embolic-risk patient is the classic signal for mesenteric ischemia_
- **MUST** — Peritoneal signs (rigidity, percussion tenderness, rebound, cough test)  
  _Rigidity and percussion tenderness have the strongest likelihood ratios for peritonitis and perforation_
- **MUST** — Palpate for a pulsatile, expansile abdominal mass and check femoral pulses bilaterally  
  _Abdominal palpation detects most large AAAs; asymmetric femoral pulses raise concern for rupture or dissection_
- should — Ask: prior abdominal surgery, vomiting, last flatus and bowel movement; inspect for distension and check hernia orifices  
  _Adhesions and hernias cause most small bowel obstructions; obstipation and distension support it_
- should — Digital rectal examination (DRE) - for blood  
  _Bloody stool supports bowel ischemia_
- should — Repeat vital signs; Orthostatic vital signs (supine to standing at 1 and 3 min) only if hemodynamically stable  
  _Tachycardia out of proportion and emerging hypotension mark a surgical abdomen_

- Off-bedside OK: Lactate; CT angiography of the abdomen; Upright chest X-ray for free air; Surgical and vascular consult; Type and screen
- Should NOT: Enema or laxative before peritoneal exam; Reassurance based on a soft abdomen without serial exam; Attributing the tachycardia to AF and rate-controlling without abdominal reassessment
- Underspecified flag: False
- **Perturbation** (comorbidity: AF not anticoagulated -> known 5.2 cm AAA under surveillance): 79M with known 5.2 cm AAA under surveillance, sudden severe diffuse abdominal pain 1h, RN says belly soft, HR 118, BP 128/76  
  → AAA rupture becomes the leading differential; pulsatile mass palpation and bilateral femoral pulses remain must-have and lead the card; the back or flank pain question becomes must-have; pain-out-of-proportion assessment drops to should-still-include; rectal exam for blood drops.
- **Noise:** Rm 7-14: 79yo male retired machinist, afib no blood thinners, abrupt severe pain all over abdomen for the last hour, nurse thinks abdomen soft, pulse 118 and pressure 128/76  
  → None. Card should be substantially identical to base.

### weakness_002  (weakness; dx: spinal_cord_compression, cauda_equina, gbs, electrolyte_hypokalemia_hypophosphatemia)
**Input:** 54M metastatic prostate CA admitted for pain control, overnight says legs heavy, trouble standing, mid-back pain worse

- **MUST** — Sensory level to pinprick and temperature on the trunk, and vibration sense in the legs  
  _A sensory level localizes cord compression and is the single most useful bedside finding for a myelopathy_
- **MUST** — Deep tendon reflexes in the legs, plantar responses (Babinski), and tone  
  _Hyperreflexia and extensor plantars indicate cord compression; areflexia points to GBS or cauda equina_
- **MUST** — Saddle sensation, digital rectal examination (DRE) - anal tone, and bladder percussion/palpation for retention  
  _Saddle anesthesia, reduced anal tone, and painless retention are the red flags for cauda equina and lower cord involvement_
- should — Spinal percussion tenderness and ask whether pain is worse lying flat or at night  
  _Localizes the vertebral level of metastatic involvement_
- should — Ask: onset and progression, bowel or bladder change, and whether weakness is symmetric; test hip flexion strength and sit-to-stand  
  _Defines pattern and speed of progression; bilateral symmetric leg weakness with back pain in cancer is cord compression until proven otherwise_
- should — Medication review (MAR): steroid, opioid, and diuretic dose changes  
  _Steroid myopathy and hypokalemia are treatable confounders in this population_

- Off-bedside OK: Whole-spine MRI with contrast; Bladder scan for post-void residual; Basic metabolic panel, phosphate, magnesium; Dexamethasone and spine/oncology consult once compression suspected
- Should NOT: Increasing opioids for back pain before a neurologic exam; Plain spine films as a substitute for neurologic examination; Waiting for a morning MRI slot before examining for a sensory level and retention
- Underspecified flag: False
- **Perturbation** (comorbidity: metastatic prostate cancer -> Campylobacter gastroenteritis 2 weeks ago): 54M with Campylobacter gastroenteritis 2 weeks ago, admitted for dehydration, overnight says legs heavy, trouble standing, mid-back pain worse  
  → GBS becomes the leading differential; reflexes (areflexia) remain must-have; single breath count or forced vital capacity for respiratory muscle strength and ask about ascending pattern and paresthesias become must-have; sensory level and spinal percussion tenderness drop to should-still-include.
- **Noise:** Bed 3-8, fifty-four year old male, retired electrician, metastatic prostate cancer in for pain management, tonight reports his legs feel heavy and he struggles to stand up, and the mid-back pain has escalated  
  → None. Card should be substantially identical to base.

## Where to look

- Full id list: `discriminator_ids.json` (sorted priority → cardiology-first). Batches: `records/batches.json`.
- All cases: `benchmark/cases/*.json`; critic reports: `benchmark/critique_part1.md`, `critique_part2.md`, `critique_recheck.md`.
- Every non-owner decision so far: `DECISIONS.md`. Timeline: `RUNLOG.md`.
