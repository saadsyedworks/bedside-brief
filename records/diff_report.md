# Extraction diff report

58 ids; 2 agree, 42 partial, 14 disagree, 0 single-packet.

## Suggested verification order

1. `exam_breath_sounds_unilateral_absent` — disagree — 2 flag(s)
2. `exam_calf_asymmetry_gt3cm` — disagree — 2 flag(s)
3. `exam_jvp_elevated` — disagree — 2 flag(s)
4. `exam_percussion_dullness` — disagree — 2 flag(s)
5. `exam_s3_gallop` — disagree — 2 flag(s)
6. `exam_tachypnea_rr_gt24` — disagree — 2 flag(s)
7. `exam_wheezing` — disagree — 3 flag(s)
8. `hx_alcohol_use_withdrawal_timing` — disagree — 3 flag(s)
9. `hx_exertional_chest_pain` — disagree — 2 flag(s)
10. `hx_pain_radiation_both_arms` — disagree — 2 flag(s)
11. `hx_palpitations_before_syncope` — disagree — 2 flag(s)
12. `hx_pleuritic_chest_pain` — disagree — 2 flag(s)
13. `hx_pnd` — disagree — 2 flag(s)
14. `hx_syncope_supine` — disagree — 2 flag(s)
15. `exam_abdominojugular_reflux` — partial — 1 flag(s)
16. `exam_ascites_flank_dullness_fluid_wave` — partial — 1 flag(s)
17. `exam_bp_differential_arms` — partial — 1 flag(s)
18. `exam_capillary_refill` — partial — 1 flag(s)
19. `exam_carotid_upstroke_delayed` — partial — 1 flag(s)
20. `exam_chest_wall_tenderness_reproducible` — partial — 1 flag(s)
21. `exam_cirrhosis_stigmata` — partial — 1 flag(s)
22. `exam_egophony` — partial — 1 flag(s)
23. `exam_fatigable_ptosis_sustained_upgaze` — partial — 1 flag(s)
24. `exam_melena_rectal_exam` — partial — 1 flag(s)
25. `exam_murmur_late_peaking_systolic` — partial — 3 flag(s)
26. `exam_orthostatic_vitals` — partial — 1 flag(s)
27. `exam_peripheral_edema_pitting` — partial — 1 flag(s)
28. `exam_pulmonary_crackles` — partial — 1 flag(s)
29. `exam_pulsatile_abdominal_mass` — partial — 2 flag(s)
30. `exam_pulse_deficit` — partial — 1 flag(s)
31. `exam_pulsus_paradoxus` — partial — 2 flag(s)
32. `exam_shifting_dullness` — partial — 1 flag(s)
33. `fn_murmur_valsalva_standing_louder` — partial — 1 flag(s)
34. `fn_tap_out_rhythm_regular` — agree — 0 flag(s)
35. `hx_exertional_syncope` — partial — 1 flag(s)
36. `hx_neck_pounding_frog_sign` — partial — 1 flag(s)
37. `hx_orthopnea` — partial — 1 flag(s)
38. `hx_pain_abrupt_maximal_onset` — partial — 1 flag(s)
39. `hx_pain_tearing_ripping` — partial — 1 flag(s)
40. `hx_palpitations_abrupt_onset_offset` — agree — 0 flag(s)
41. `hx_postural_dizziness` — partial — 1 flag(s)
42. `hx_syncope_prodrome` — partial — 1 flag(s)
43. `hx_vte_risk_factors` — partial — 1 flag(s)
44. `exam_ascending_symmetric_weakness_areflexia` — partial — 1 flag(s)
45. `exam_cellulitis_unilateral_warmth_border` — partial — 1 flag(s)
46. `exam_pulse_irregularly_irregular` — partial — 5 flag(s)
47. `fn_passive_leg_raise` — partial — 1 flag(s)
48. `fn_single_breath_count` — partial — 1 flag(s)
49. `hx_dizziness_timing_triggers` — partial — 1 flag(s)
50. `hx_post_event_confusion` — partial — 3 flag(s)
51. `pocus_aaa_aorta_diameter` — partial — 1 flag(s)
52. `pocus_dvt_compression` — partial — 1 flag(s)
53. `pocus_ivc_collapsibility` — partial — 1 flag(s)
54. `pocus_lung_b_lines` — partial — 1 flag(s)
55. `pocus_lung_sliding_absent` — partial — 1 flag(s)
56. `pocus_lv_function_eyeball` — partial — 2 flag(s)
57. `pocus_pericardial_effusion` — partial — 1 flag(s)
58. `pocus_rv_dilation` — partial — 1 flag(s)

## Per-id detail

### exam_breath_sounds_unilateral_absent  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### exam_calf_asymmetry_gt3cm  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### exam_jvp_elevated  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=1 B=3 (population split or omission)

### exam_percussion_dullness  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=3 B=3 (population split or omission)

### exam_s3_gallop  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=3 B=6 (population split or omission)

### exam_tachypnea_rr_gt24  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs partially_quantified
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### exam_wheezing  (extractor-A, extractor-B) — **disagree**
- SILENT COMPUTATION? (extractor-B): estimates[2] LR+ equals sens/(1-spec) but computed=false
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=1 B=3 (population split or omission)

### hx_alcohol_use_withdrawal_timing  (extractor-A, extractor-B) — **disagree**
- SECONDARY SOURCE? (extractor-B): sources[4] kind=guideline on a quantified record
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=4 B=3 (population split or omission)

### hx_exertional_chest_pain  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs partially_quantified
- ESTIMATE SET DIFFERS: A=3 B=2 (population split or omission)

### hx_pain_radiation_both_arms  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs partially_quantified
- ESTIMATE SET DIFFERS: A=4 B=4 (population split or omission)

### hx_palpitations_before_syncope  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs not_quantified
- ESTIMATE SET DIFFERS: A=1 B=0 (population split or omission)

### hx_pleuritic_chest_pain  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=3 B=1 (population split or omission)

### hx_pnd  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: partially_quantified vs quantified
- ESTIMATE SET DIFFERS: A=3 B=1 (population split or omission)

### hx_syncope_supine  (extractor-A, extractor-B) — **disagree**
- STATUS MISMATCH: quantified vs not_quantified
- ESTIMATE SET DIFFERS: A=1 B=0 (population split or omission)

### exam_abdominojugular_reflux  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### exam_ascites_flank_dullness_fluid_wave  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=1 (population split or omission)

### exam_bp_differential_arms  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=1 (population split or omission)

### exam_capillary_refill  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=5 (population split or omission)

### exam_carotid_upstroke_delayed  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### exam_chest_wall_tenderness_reproducible  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=3 (population split or omission)

### exam_cirrhosis_stigmata  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=1 (population split or omission)

### exam_egophony  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=1 (population split or omission)

### exam_fatigable_ptosis_sustained_upgaze  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=1 (population split or omission)

### exam_melena_rectal_exam  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=3 (population split or omission)

### exam_murmur_late_peaking_systolic  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-A): estimates[1] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[3] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=5 (population split or omission)

### exam_orthostatic_vitals  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### exam_peripheral_edema_pitting  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=1 (population split or omission)

### exam_pulmonary_crackles  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=5 (population split or omission)

### exam_pulsatile_abdominal_mass  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-B): estimates[4] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=5 B=5 (population split or omission)

### exam_pulse_deficit  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=3 (population split or omission)

### exam_pulsus_paradoxus  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-B): estimates[2] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### exam_shifting_dullness  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=1 (population split or omission)

### fn_murmur_valsalva_standing_louder  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=1 (population split or omission)

### fn_tap_out_rhythm_regular  (extractor-A, extractor-B) — **agree**
- no flags

### hx_exertional_syncope  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### hx_neck_pounding_frog_sign  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=3 (population split or omission)

### hx_orthopnea  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=1 (population split or omission)

### hx_pain_abrupt_maximal_onset  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### hx_pain_tearing_ripping  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=1 (population split or omission)

### hx_palpitations_abrupt_onset_offset  (extractor-A, extractor-B) — **agree**
- no flags

### hx_postural_dizziness  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### hx_syncope_prodrome  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=6 B=3 (population split or omission)

### hx_vte_risk_factors  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=7 (population split or omission)

### exam_ascending_symmetric_weakness_areflexia  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### exam_cellulitis_unilateral_warmth_border  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### exam_pulse_irregularly_irregular  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-A): estimates[0] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-A): estimates[1] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[0] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[1] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

### fn_passive_leg_raise  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=4 (population split or omission)

### fn_single_breath_count  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=4 B=6 (population split or omission)

### hx_dizziness_timing_triggers  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=1 (population split or omission)

### hx_post_event_confusion  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-A): estimates[1] LR+ equals sens/(1-spec) but computed=false
- SILENT COMPUTATION? (extractor-B): estimates[0] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=4 B=4 (population split or omission)

### pocus_aaa_aorta_diameter  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=1 B=2 (population split or omission)

### pocus_dvt_compression  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=5 B=4 (population split or omission)

### pocus_ivc_collapsibility  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### pocus_lung_b_lines  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=3 (population split or omission)

### pocus_lung_sliding_absent  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=3 B=4 (population split or omission)

### pocus_lv_function_eyeball  (extractor-A, extractor-B) — **partial**
- SILENT COMPUTATION? (extractor-A): estimates[0] LR+ equals sens/(1-spec) but computed=false
- ESTIMATE SET DIFFERS: A=2 B=5 (population split or omission)

### pocus_pericardial_effusion  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=4 (population split or omission)

### pocus_rv_dilation  (extractor-A, extractor-B) — **partial**
- ESTIMATE SET DIFFERS: A=2 B=2 (population split or omission)

