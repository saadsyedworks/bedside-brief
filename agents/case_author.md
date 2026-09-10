# Case-author subagent

Author benchmark cases for Bedside Brief BEFORE the evidence library exists. Do not consult `records/`. Follow `benchmark_case_template.json` exactly.

For each presentation in `vocab.json`, write 3 base cases spanning different diagnostic branches (e.g., syncope: structural, arrhythmic, orthostatic). Each base case gets:
- `input_oneliner`: sparse, triage-style, as a nocturnist would receive it. 12–30 words. No diagnosis stated.
- `intended_bedside_differential`: 2–4 items from vocab.
- `reference_targets_freetext`: 3–6 items, each a history question, exam maneuver, or functional test, with a one-line rationale and `must_have` true/false. Write these from clinical judgment and the diagnostic-accuracy literature you know; do not reference the library.
- `off_bedside_acceptable`: items that are fine to recommend (e.g., ECG) but not bedside.
- `should_not_recommend`: 1–3 items that would be inappropriate, unsafe, or a substitute for examination.
- `underspecified_flag_expected`: true only if the one-liner is deliberately too sparse to rank (include ~1 such case per 4 presentations).
- `perturbation_pair`: change exactly ONE clinically meaningful feature; state `expected_change` concretely.
- `noise_variant`: reword and add non-contributory detail; `expected_change: "None."`

Save each as `benchmark/cases/{presentation}_{nnn}.json`. Leave `reference_targets_mapped`, `authored_at`, `frozen_commit` empty for the pipeline to fill.
