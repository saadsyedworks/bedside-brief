# Evaluation Rubric — Bedside Brief v1 (abstract)

## Arms
- **A. Bedside Brief** — full pipeline (parse → retrieve → LLM rank → render).
- **B. Retrieval-only** — same store, all matching records rendered in fixed order, truncated to card limits. Tests whether the LLM ranking layer earns its place.
- **C. Generic LLM** — unconstrained prompt: "Given this presentation, what history, physical examination, and bedside tests should I perform? Include any diagnostic performance data you know." Same model as the ranker. Parsed into item list by the same deterministic parser used for A/B.

Run A and C on every case. Run B on every case (cheap). Report A vs C as primary, A vs B as ablation.

## Scoring units
Each recommended item is one unit. Items are classified by a deterministic rule before any judgment:
- **Bedside** = history question, exam maneuver, functional test, POCUS.
- **Off-bedside** = lab, imaging, ECG, consult, monitoring, admission/disposition, treatment.
(ECG counted off-bedside for consistency; report a sensitivity analysis with ECG as bedside.)

## Metrics — MECHANICAL (no reviewer judgment)
| Metric | Definition | Arms |
|---|---|---|
| Bedside share | bedside items / all items | A, B, C |
| Target recall | must_have reference targets present / must_have targets | A, B, C |
| Target recall (all) | any reference target present / all targets | A, B, C |
| Library coverage | reference targets that map to ANY store record / all targets (measures store completeness; computed once, arm-independent) | store |
| Evidence fidelity | displayed numbers/citations exactly matching the linked verified record / all displayed numbers | A, B |
| Unsupported quantitative claim rate | numeric claims with no verified record / all numeric claims | A, B, C |
| Perturbation responsiveness | expected_change items realized in perturbation pair output | A, B, C |
| Noise stability | Jaccard(base items, noise-variant items) | A, B, C |
| Brevity | items per card; ≤ limits (pass/fail) | A, B, C |
| Not-quantified share | verified records with evidence_status = not_quantified / verified records | store |

## Metrics — JUDGED (single author-reviewer, disclosed)
| Metric | Definition | Scale |
|---|---|---|
| Relevance | item is clinically useful for THIS case | relevant / marginal / irrelevant |
| Safety | item appears on should_not_recommend, is contraindicated, misleading, or out of scope | flag / no flag |

Reviewer scores items blinded to arm where feasible (shuffle items, strip formatting).

## Precomputed reporting for the abstract
- N cases, N perturbation pairs, N noise variants.
- N verified of M extracted records; not-quantified share.
- Bedside share A vs C (headline), target recall A vs C, unsupported-claim rate A vs C.
- Ablation: recall and relevance A vs B.
- Error analysis: top 5 failure modes of A.

## What the abstract may claim
Development + technical validation on a frozen synthetic benchmark. Not: bedside time, real-patient accuracy, outcomes, or behavior change.

## Freeze protocol
1. Author cases + free-text targets + perturbation/noise pairs.
2. Commit. Record hash in each case's `frozen_commit`.
3. Map targets to record ids. Commit again.
4. Run all arms. No edits to cases or targets afterward. Product fixes allowed; re-run the frozen set and report both runs.
