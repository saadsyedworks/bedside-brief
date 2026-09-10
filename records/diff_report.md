# Extraction diff report

24 ids; 0 agree, 15 partial, 3 disagree, 6 single-packet.

## Suggested verification order

1. `hx_exertional_chest_pain` — disagree — 2 flag(s)
2. `hx_pain_radiation_both_arms` — disagree — 2 flag(s)
3. `hx_pleuritic_chest_pain` — disagree — 2 flag(s)
4. `exam_abdominojugular_reflux` — single_packet — 0 flag(s)
5. `exam_bp_differential_arms` — partial — 1 flag(s)
6. `exam_capillary_refill` — partial — 1 flag(s)
7. `exam_carotid_upstroke_delayed` — partial — 1 flag(s)
8. `exam_chest_wall_tenderness_reproducible` — partial — 1 flag(s)
9. `exam_jvp_elevated` — single_packet — 0 flag(s)
10. `exam_murmur_late_peaking_systolic` — partial — 3 flag(s)
11. `exam_orthostatic_vitals` — partial — 1 flag(s)
12. `exam_peripheral_edema_pitting` — partial — 1 flag(s)
13. `exam_pulmonary_crackles` — single_packet — 0 flag(s)
14. `exam_pulse_deficit` — partial — 1 flag(s)
15. `exam_pulsus_paradoxus` — partial — 2 flag(s)
16. `exam_s3_gallop` — single_packet — 0 flag(s)
17. `fn_murmur_valsalva_standing_louder` — partial — 1 flag(s)
18. `hx_exertional_syncope` — partial — 1 flag(s)
19. `hx_orthopnea` — single_packet — 0 flag(s)
20. `hx_pain_tearing_ripping` — partial — 1 flag(s)
21. `hx_pnd` — single_packet — 0 flag(s)
22. `hx_syncope_prodrome` — partial — 1 flag(s)
23. `exam_pulse_irregularly_irregular` — partial — 5 flag(s)
24. `fn_passive_leg_raise` — partial — 1 flag(s)

## Per-id detail

### hx_exertional_chest_pain  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs partially_quantified
- ESTIMATE SET DIFFERS: A=3 B=2 (population split or omission)

### hx_pain_radiation_both_arms  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs partially_quantified
- ESTIMATE SET DIFFERS: A=4 B=4 (population split or omission)

### hx_pleuritic_chest_pain  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=3 B=1 (population split or omission)

### exam_abdominojugular_reflux  (extractor-A) — **single_packet**
- no flags

### exam_bp_differential_arms  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=1 (population split or omission)

### exam_capillary_refill  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=5 (population split or omission)

### exam_carotid_upstroke_delayed  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### exam_chest_wall_tenderness_reproducible  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=3 (population split or omission)

### exam_jvp_elevated  (extractor-A) — **single_packet**
- no flags

### exam_murmur_late_peaking_systolic  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-A): estimates[1] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[3] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=5 (population split or omission)

### exam_orthostatic_vitals  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### exam_peripheral_edema_pitting  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=1 (population split or omission)

### exam_pulmonary_crackles  (extractor-A) — **single_packet**
- no flags

### exam_pulse_deficit  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=3 (population split or omission)

### exam_pulsus_paradoxus  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-B): estimates[2] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### exam_s3_gallop  (extractor-A) — **single_packet**
- no flags

### fn_murmur_valsalva_standing_louder  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=1 (population split or omission)

### hx_exertional_syncope  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### hx_orthopnea  (extractor-A) — **single_packet**
- no flags

### hx_pain_tearing_ripping  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=1 (population split or omission)

### hx_pnd  (extractor-A) — **single_packet**
- no flags

### hx_syncope_prodrome  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=6 B=3 (population split or omission)

### exam_pulse_irregularly_irregular  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-A): estimates[0] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-A): estimates[1] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[0] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[1] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### fn_passive_leg_raise  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=4 (population split or omission)

