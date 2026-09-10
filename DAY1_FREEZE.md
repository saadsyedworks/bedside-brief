# Bedside Brief — Day 1 Freeze (2026-09-09)

Decisions locked for the abstract build. Change only by editing this file with a dated note.

## Scope
- Users: inpatient internal medicine — residents and hospitalists.
- Presentations (12): dyspnea/hypoxemia; chest pain; dizziness/vertigo; syncope/presyncope; palpitations/tachycardia; edema/volume overload; hypotension/shock; altered mental status; abdominal pain; fever/suspected infection; weakness (focal or generalized); AKI/oliguria.
- Discriminator types: history, exam, functional. POCUS: [OWNER DECISION — in or v2]. Schema supports it either way.
- Card limits: ≤4 Ask, ≤4 Examine, ≤3 POCUS (if in). Default card must read in ~20 s.

## Roles
- Single author. Single clinical reviewer (same person). Disclosed as a limitation in the abstract.
- AI agents: extraction, drafting, red-team. Never the verifier of record.

## Evidence rules
- Record tiers: `extracted` → `verified`. Only `verified` renders in production and enters the evaluation.
- Verification = owner has read the source location and confirmed the number.
- Two independent extractions per record; disagreements reviewed first.
- Source hierarchy: (1) JAMA Rational Clinical Examination series / diagnostic-accuracy meta-analyses; (2) prospective diagnostic-accuracy primary studies; (3) guideline/expert statements → tagged `not_quantified`. McGee and narrative reviews are indexes, never the cited source of a number.
- Multiple estimates per discriminator when performance differs by population/setting. Never one "universal" number.
- `not_quantified` is a first-class state and its proportion is reported.

## Architecture (unchanged from brief)
- LLM parses one-liner → deterministic retrieval over curated store → LLM ranks under limits → deterministic render from stored fields → audit link per claim.
- Retrieval is keyed on the parser's `differentials` (primary) and `indication_tags` (secondary); `presentations` is a filter, not the key. Cross-presentation retrieval is expected. (Decided 2026-09-09.)
- Parser output contract: chief complaint, time course, modifiers, weighted candidate differentials (≥1, ≤6), indication tags, and a list of missing features that would change the ranking.
- LLM never emits sens/spec/LR/citation text. Validator blocks any card containing a number not present in a `verified` record.
- Underspecified input rule: if the parser flags a missing feature that would change ranking (e.g., exertional vs positional), the card surfaces an "ask first" line rather than guessing.

## Evaluation (see evaluation_rubric.md)
- Benchmark authored and reference targets written BLIND, before the library is queried. Frozen by git commit + timestamp before first eval run.
- Arms: (A) Bedside Brief; (B) retrieval-only, no LLM ranking; (C) generic unconstrained LLM prompt.
- Headline: bedside vs off-bedside share of recommendations, A vs C.
- Abstract numbers computed only on the `verified` subset. Report "N verified of M extracted."

## Deadline plan
- Tue Sep 15: abstract with preliminary numbers on verified subset.
- Nov 13: poster/oral with full evaluation; owner completes remaining verification and any expanded review.
