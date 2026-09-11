# Error analysis — arm A (108 case inputs)

## Top 5 failure modes

1. **missing must have targets** — 96 targets
2. **should not recommend hits** — 5 cases
3. **ask first false negatives** — 2 cases
4. **ask first false positives** — 0 cases
5. **brevity failures** — 0 cases

## Detail

### missing must have targets (96 targets)
- abdominal_pain: 2 missing — RLQ tenderness (McBurney point) ×1; Palpate for a pulsatile, expansile abdominal mass ×1
- aki: 10 missing — Orthostatic vital signs (supine to standing at 1 and 3 min) ×5; Abdominojugular reflux ×3; Medication review (MAR): anticholinergics, opioids, alpha-agonists ×2
- ams: 13 missing — Suprapubic tenderness and Costovertebral angle (CVA) tenderness (urinary source) ×3; Abdominal tenderness (SBP) ×3; Digital rectal examination (DRE) for melena ×3
- chest_pain: 9 missing — S3 gallop ×3; Palpate the chest wall and costochondral junctions for fully reproducible tenderness ×3; Radial/femoral pulse deficit ×2
- dizziness: 2 missing — HINTS exam (head impulse, nystagmus, test of skew) ×1; Dix-Hallpike maneuver on each side, observing latency, duration, and direction of nystagmus ×1
- dyspnea: 10 missing — S3 gallop (third heart sound) at the apex in left lateral decubitus ×3; Ask about known COPD diagnosis or prior spirometry, home inhalers, and prior exacerbations needing steroids or intubation ×3; Forced expiratory time (timed forced exhalation, >=9 s) ×3
- edema: 5 missing — S3 gallop (third heart sound) at the apex in left lateral decubitus ×3; Calf circumference asymmetry >3 cm (10 cm below tibial tuberosity) ×1; Wells DVT items on history and exam: bedridden >3 days, active cancer, prior VTE, recent surgery, pitting edema confined to the symptomatic leg, collateral superficial veins ×1
- fever: 4 missing — Inspect surgical wound for erythema, warmth, drainage, dehiscence, and tenderness beyond the incision ×3; Cardiac auscultation for a new or changed murmur ×1
- hypotension: 13 missing — Mental status and respiratory rate at the bedside (qSOFA elements) ×3; Ask about melena, hematemesis, and hematochezia ×3; Digital rectal examination (DRE) for melena ×3
- palpitations: 15 missing — JVP (jugular venous pressure) ×3; Bedside hemodynamic stability: mentation, chest pain, dyspnea, Capillary refill time, skin temperature ×3; Cannon a waves in the jugular venous pulse and variable intensity of S1 (AV dissociation) ×3
- syncope: 6 missing — Dynamic auscultation: murmur intensity with Valsalva and squat-to-stand (louder with Valsalva or standing suggests HCM, softer suggests AS) ×3; Dry axilla / mucous membranes ×2; Witness account: duration, color, jerking, tongue biting, incontinence, post-event confusion (from nurse) ×1
- weakness: 7 missing — Establish last-known-well time precisely ×3; Ask: focal versus generalized, sudden versus gradual onset, new today or progressive since admission, and whether the problem is weakness, dizziness, or pain on standing ×3; Proximal strength: sit-to-stand without arms, hip flexion against resistance, arms held above head ×1
- {"case_id": "abdominal_pain_001_p1", "target": "RLQ tenderness (McBurney point)"}
- {"case_id": "abdominal_pain_003_n1", "target": "Palpate for a pulsatile, expansile abdominal mass"}
- {"case_id": "aki_001", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_001", "target": "Abdominojugular reflux"}
- {"case_id": "aki_001_n1", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_001_n1", "target": "Abdominojugular reflux"}
- {"case_id": "aki_001_p1", "target": "Abdominojugular reflux"}
- {"case_id": "aki_002", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_002_n1", "target": "Medication review (MAR): anticholinergics, opioids, alpha-agonists"}
- {"case_id": "aki_002_p1", "target": "Medication review (MAR): anticholinergics, opioids, alpha-agonists"}
- {"case_id": "aki_002_p1", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_003", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}

### should not recommend hits (5 cases)
- {"case_id": "aki_003", "item": "Muscle pain/weakness, prolonged immobilization or exertion, dark cola-colored urine", "should_not_recommend": "NSAIDs for muscle pain"}
- {"case_id": "aki_003_n1", "item": "Muscle pain/weakness, prolonged immobilization or exertion, dark cola-colored urine", "should_not_recommend": "NSAIDs for muscle pain"}
- {"case_id": "aki_003_p1", "item": "Muscle pain/weakness, prolonged immobilization or exertion, dark cola-colored urine", "should_not_recommend": "NSAIDs for muscle pain"}
- {"case_id": "hypotension_002", "item": "Orthostatic vitals: SBP drop >=20 / DBP >=10 mmHg or pulse increment >=30/min at 1-3 min standing", "should_not_recommend": "Standing the patient for orthostatic vital signs while supine SBP remains <90"}
- {"case_id": "hypotension_002_p1", "item": "Orthostatic vitals: SBP drop >=20 / DBP >=10 mmHg or pulse increment >=30/min at 1-3 min standing", "should_not_recommend": "Standing the patient for orthostatic vital signs while supine SBP remains <90"}

### ask first false negatives (2 cases)
- weakness_003
- weakness_003_n1

### ask first false positives (0 cases)
- none

### brevity failures (0 cases)
- none

### empty cards (0 cases)
- none

### pipeline errors (0 cases)
- none

### unsupported quantitative claims (0 numbers)
- none

### validator blocked items (0 items)
- none
