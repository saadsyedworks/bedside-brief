# Error analysis — arm A (108 case inputs)

## Top 5 failure modes

1. **missing must have targets** — 91 targets
2. **ask first false negatives** — 3 cases
3. **ask first false positives** — 0 cases
4. **brevity failures** — 0 cases
5. **empty cards** — 0 cases

## Detail

### missing must have targets (91 targets)
- abdominal_pain: 1 missing — Murphy sign (inspiratory arrest on RUQ palpation) ×1
- aki: 12 missing — Orthostatic vital signs (supine to standing at 1 and 3 min) ×7; Abdominojugular reflux ×3; Medication review (MAR): anticholinergics, opioids, alpha-agonists ×2
- ams: 13 missing — Suprapubic tenderness and Costovertebral angle (CVA) tenderness (urinary source) ×3; Abdominal tenderness (SBP) ×3; Digital rectal examination (DRE) for melena ×3
- chest_pain: 8 missing — S3 gallop ×3; Palpate the chest wall and costochondral junctions for fully reproducible tenderness ×2; Radial/femoral pulse deficit ×1
- dizziness: 3 missing — Gait assessment: can the patient stand and walk unaided (sit unsupported; truncal ataxia) ×2; Dix-Hallpike maneuver on each side, observing latency, duration, and direction of nystagmus ×1
- dyspnea: 8 missing — Ask about known COPD diagnosis or prior spirometry, home inhalers, and prior exacerbations needing steroids or intubation ×3; Forced expiratory time (timed forced exhalation, >=9 s) ×3; S3 gallop (third heart sound) at the apex in left lateral decubitus ×2
- edema: 5 missing — S3 gallop (third heart sound) at the apex in left lateral decubitus ×3; Calf circumference asymmetry >3 cm (10 cm below tibial tuberosity) ×1; Wells DVT items on history and exam: bedridden >3 days, active cancer, prior VTE, recent surgery, pitting edema confined to the symptomatic leg, collateral superficial veins ×1
- fever: 3 missing — Inspect surgical wound for erythema, warmth, drainage, dehiscence, and tenderness beyond the incision ×3
- hypotension: 12 missing — Mental status and respiratory rate at the bedside (qSOFA elements) ×3; Capillary refill time (>3 s), skin mottling over the knees, cool extremities ×2; Ask about melena, hematemesis, and hematochezia ×2
- palpitations: 15 missing — JVP (jugular venous pressure) ×3; Bedside hemodynamic stability: mentation, chest pain, dyspnea, Capillary refill time, skin temperature ×3; Cannon a waves in the jugular venous pulse and variable intensity of S1 (AV dissociation) ×3
- syncope: 5 missing — Dry axilla / mucous membranes ×2; Dynamic auscultation: murmur intensity with Valsalva and squat-to-stand (louder with Valsalva or standing suggests HCM, softer suggests AS) ×1; Medication review (MAR): sotalol dose and timing, other QT-prolonging or AV-nodal agents, recent additions ×1
- weakness: 6 missing — Establish last-known-well time precisely ×3; Ask: focal versus generalized, sudden versus gradual onset, new today or progressive since admission, and whether the problem is weakness, dizziness, or pain on standing ×3
- {"case_id": "abdominal_pain_002_p1", "target": "Murphy sign (inspiratory arrest on RUQ palpation)"}
- {"case_id": "aki_001", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_001", "target": "Abdominojugular reflux"}
- {"case_id": "aki_001_n1", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_001_n1", "target": "Abdominojugular reflux"}
- {"case_id": "aki_001_p1", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_001_p1", "target": "Abdominojugular reflux"}
- {"case_id": "aki_002", "target": "Medication review (MAR): anticholinergics, opioids, alpha-agonists"}
- {"case_id": "aki_002", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_002_p1", "target": "Medication review (MAR): anticholinergics, opioids, alpha-agonists"}
- {"case_id": "aki_002_p1", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}
- {"case_id": "aki_003", "target": "Orthostatic vital signs (supine to standing at 1 and 3 min)"}

### ask first false negatives (3 cases)
- dizziness_003_n1
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

### should not recommend hits (0 cases)
- none

### unsupported quantitative claims (0 numbers)
- none

### validator blocked items (0 items)
- none
