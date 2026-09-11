# Error analysis — arm A (9 case inputs)

## Top 5 failure modes

1. **missing must have targets** — 22 targets
2. **ask first false negatives** — 0 cases
3. **ask first false positives** — 0 cases
4. **brevity failures** — 0 cases
5. **empty cards** — 0 cases

## Detail

### missing must have targets (22 targets)
- syncope: 22 missing — Dynamic auscultation: murmur intensity with Valsalva and squat-to-stand (louder with Valsalva or standing suggests HCM, softer suggests AS) ×3; Ask about prodrome and palpitations before the event ×3; Ask about prodrome (none vs palpitations vs lightheadedness), what she was doing (lying vs standing), and duration of unconsciousness ×3
- {"case_id": "syncope_001", "target": "Dynamic auscultation: murmur intensity with Valsalva and squat-to-stand (louder with Valsalva or standing suggests HCM, softer suggests AS)"}
- {"case_id": "syncope_001", "target": "Ask about prodrome and palpitations before the event"}
- {"case_id": "syncope_001_n1", "target": "Dynamic auscultation: murmur intensity with Valsalva and squat-to-stand (louder with Valsalva or standing suggests HCM, softer suggests AS)"}
- {"case_id": "syncope_001_n1", "target": "Ask about prodrome and palpitations before the event"}
- {"case_id": "syncope_001_p1", "target": "Characterize the murmur: late-peaking, radiation to carotids, soft or absent S2, slow or delayed carotid upstroke"}
- {"case_id": "syncope_001_p1", "target": "Dynamic auscultation: murmur intensity with Valsalva and squat-to-stand (louder with Valsalva or standing suggests HCM, softer suggests AS)"}
- {"case_id": "syncope_001_p1", "target": "Ask about prodrome and palpitations before the event"}
- {"case_id": "syncope_002", "target": "Ask about prodrome (none vs palpitations vs lightheadedness), what she was doing (lying vs standing), and duration of unconsciousness"}
- {"case_id": "syncope_002", "target": "Witness account: duration, color, jerking, tongue biting, incontinence, post-event confusion (from nurse)"}
- {"case_id": "syncope_002", "target": "Medication review (MAR): sotalol dose and timing, other QT-prolonging or AV-nodal agents, recent additions"}
- {"case_id": "syncope_002_n1", "target": "Ask about prodrome (none vs palpitations vs lightheadedness), what she was doing (lying vs standing), and duration of unconsciousness"}
- {"case_id": "syncope_002_n1", "target": "Witness account: duration, color, jerking, tongue biting, incontinence, post-event confusion (from nurse)"}

### ask first false negatives (0 cases)
- none

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
