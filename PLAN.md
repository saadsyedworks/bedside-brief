# PLAN — work top to bottom, check off, keep current

> ## STATUS: PAUSED 2026-09-12 — not submitting to the Nov 2026 Conference in Bedside Medicine.
>
> Owner's call, and the reasoning is on the record: the abstract is a technical/methods
> validation, and the Northwestern conference is a bedside clinical-skills meeting. The
> mismatch is in the work, not the wording — there is no patient, no user other than the
> author, and no clinical or educational outcome to report, so re-framing the prose would
> have dressed a methods paper as an innovation. Registration is ~$900 at the regular tier,
> which is not worth paying for a poster on an unfinished tool.
>
> **Everything is committed, pushed and reproducible.** Nothing here decays while it sits.
> The abstract stays in `abstract.md` as the honest record of what the validation showed;
> it was never signed off (gate 4 open) and `abstract-v1` is deliberately NOT tagged.
>
> **If this is picked up again, the order that matters is:**
> 1. Deploy it and use it yourself on real admissions for a few weeks. An access gate and a
>    "not for clinical use / no PHI" disclaimer come before any public URL — neither exists yet.
> 2. Get one clinician who is not the author to use it. The project's central weakness is that
>    one person built it, wrote its 36 test cases and graded all 427 of its outputs.
> 3. Then the resident study already sketched below (exam plan with vs without the brief).
>    That is the version that belongs at a bedside-medicine meeting.
>
> For the current methods work as it stands, the right venues are diagnostic-error or
> informatics meetings (SIDM's Diagnostic Error in Medicine, AMIA, an SGIM innovations
> track) — not a clinical-skills conference. Deadlines unverified.

## Phase 0 — Taxonomy + benchmark (Day 1). GATE: owner sign-off.
- [x] Review `vocab.json`; extend differentials/tags only if a case clearly needs it; note additions in DECISIONS.md. (No extension needed: 36/36 cases and 148/148 ids validate; wish-list → owner gate, DECISIONS #9.)
- [x] Author `discriminator_ids.json` (148 ids: 80 exam / 39 history / 15 functional / 14 pocus; 77 rce_backed; anchors PubMed-confirmed; commit b419c32): ~150 ids across history/exam/functional/pocus, each with title, type, presentations[], differentials[], expected_evidence (rce_backed | likely_quantified | likely_not_quantified). Prioritize discriminators with known diagnostic-accuracy literature (JAMA Rational Clinical Examination series is the index). Cardiology and volume assessment deep.
- [x] case-author + case-critic: 3 base cases per presentation (36) [36 files / 108 inputs; 2 critic passes + 2 re-checks; frozen at 39a698e] each with 1 perturbation pair + 1 noise variant → 108 files in `benchmark/cases/`. Free-text targets only; `reference_targets_mapped` empty. Follow `benchmark_case_template.json`.
- [x] Owner gate (PHASE0_GATE.md): rulings 1–8 received and applied (DECISIONS #18). Commit → **freeze #1 = 39a698e**; hash written into every case file; `tests/test_freeze.py` guards it.

## Phase 1 — Extraction (Days 1–3, runs in background)
- [x] Build `agents/extractor.md` from `extraction_packet_spec.md`. Build `agents/redteam.md`. (Shipped in handoff; plus `tools/pubmed.py`, `tools/record_skeleton.py`, `tools/diff_report.py`.)
- [x] Run extractor-A and extractor-B over all ids, batched by presentation, cardiology first. Write to `records/extracted/`. (306 packets / 153 ids in 4 waves.)
- [x] Red-team each batch (waves 1–4 done, all 153 ids). Produce `records/diff_report.md`: per id, agreement status, flagged issues, and a suggested verification order (disagreements first, then rce_backed agreements, then rest).
- [x] Build `tools/verify_ui.py` (done; 9 tests) — owner gate pending:: side-by-side packet view with quote + location + link, one-click promote/reject/edit → writes `records/verified/{id}.json` with `verified_by`, `verified_at`. Owner gate: hand over the queue.

## Phase 2 — Pipeline (Days 2–3, parallel with extraction)
- [x] `store.py`: load/validate records against schema; SQLite index on differentials, indication_tags, presentations, type, tier.
- [x] `parser.py`: LLM → strict JSON (chief complaint, time course, modifiers, weighted differentials ≤6 from vocab, indication_tags from vocab, missing_features[]). Reject any token not in vocab.
- [x] `retrieve.py`: deterministic; candidates = verified records whose differentials ∩ parsed differentials ≠ ∅, boosted by tag overlap, filtered by presentation; pocus excluded unless enabled.
- [x] `rank.py`: LLM chooses ≤4 Ask / ≤4 Examine / ≤3 POCUS from candidate ids only; returns ids + one-line rationale per id; hard-fail on any id not in candidates.
- [x] `render.py`: card assembled from stored fields only; evidence drawer; badge from evidence_status; audit link per item; "ask first" line if missing_features non-empty and would change ranking.
- [x] `validate.py`: regex-scan rendered card for numbers; every number must exist in a linked verified record; else block and log.
- [x] `bayes.py`: deterministic pre/post-test calculator (optional view).
- [x] `api.py` + single-page UI: input box, one button, ASK/EXAMINE/POCUS sections, evidence expands on demand. Copy: "Review. Pocket the phone. See the patient."
- [x] Tests (155 total incl. freeze guard): schema validation, retrieval determinism, ranker id-containment, validator blocking, render fidelity, perturbation/noise fixtures. code-reviewer pass.

## Phase 3 — Evaluation (Day 4–5). GATE: freeze #2, then judging queue.
- [x] Map free-text targets → record ids (`reference_targets_mapped`; `benchmark/target_map.json`, 216/258 mapped, 42 gaps counted for library coverage). Commit → **freeze #2** (hash in DECISIONS #26).
- [x] `eval/arms.py`: A (full), B (retrieval-only, fixed order, truncated), C (generic LLM prompt, same model, parsed by same item parser).
- [x] `eval/metrics.py`: every mechanical metric in `evaluation_rubric.md`; ECG sensitivity analysis; **must-have recall stratified quantified vs not_quantified (gate ruling 3); MAR-review-off-bedside sensitivity analysis (gate ruling 4)**.
- [x] `eval/judging_export.py`: shuffled, arm-blinded item list (CSV) for owner relevance/safety scoring; `judging_import.py`.
- [ ] Run all arms on frozen set; write `eval/runs/{timestamp}/`. Error analysis: top 5 failure modes of A with examples.
- [ ] Owner gate: judging queue (default 12 cases × 3 arms; all cases if owner has time).

## Phase 4 — Fix + report (Day 6)
- [ ] Fix high-impact failure modes in pipeline only. Re-run frozen set. Report both runs.
- [x] `eval/report.py`: tables + figure (bedside share A vs C; recall A vs B vs C).
- [~] Draft `abstract.md` — skeleton done (2 variants, every number a traced placeholder; fill after the reportable run) (≤400 words: background, innovation, methods, results, limitations, conclusion). Every number annotated with its source file path in a comment. Owner gate.

## Phase 5 — Submit (Day 7)
- [x] Number audit: `tools/number_audit.py` cross-checks abstract numbers against run outputs (11 tests).
- [~] README with reproducibility notes (done); tag release `abstract-v1` after owner abstract sign-off.

## Fallback (trigger Sunday night if verified < 60 or end-to-end fails)
Development abstract: architecture, store statistics (N extracted, N verified, not-quantified share, presentations covered), frozen benchmark described, comparison "in progress." No comparison numbers.

## Post-abstract (Oct) — SUPERSEDED by the pause above
Written when a Nov poster was the plan. Kept because it names the right next steps in the wrong order: the human study is the point, and deployment plus a non-author user come before it. Verify remaining records; 5 cases/presentation; UI polish; small human study design (residents plan exam with vs without brief); poster.
