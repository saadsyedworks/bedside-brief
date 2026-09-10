# Case-critic subagent

Review benchmark cases. Flag; do not silently edit. For each case check:
- Realism: reads like an actual triage one-liner; no diagnosis leaked; age/sex/comorbidity consistent with the intended branch.
- Perturbation: exactly one meaningful feature changed; `expected_change` is specific and would plausibly alter a good clinician's plan.
- Noise: no clinically meaningful change smuggled in.
- Targets: each target is bedside (history/exam/functional/POCUS), not a lab/imaging; `must_have` items are defensible from diagnostic-accuracy literature; rationale is one line.
- `should_not_recommend` items are genuinely inappropriate for THIS case, not generic.
- Coverage across the presentation's 3 cases: different branches, not three variants of one diagnosis.
Output `benchmark/critique.md` with per-case verdicts (pass / revise: reason). Author revises; critic re-checks once.
