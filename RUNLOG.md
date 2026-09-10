# RUNLOG — chronological, append only

## 2026-09-10
- 00:47 Freeze package unpacked to repo root; `.env` created and confirmed gitignored; commit `332619c` "Bedside Brief: Day 1 freeze package" pushed to `claude/git-repo-setup-rvdx9z`.
- 00:50 Pre-flight FAILED: egress proxy 403 on api.openai.com and all literature hosts (Trusted network level). Reported to owner.
- 00:58 Owner switched environment to Full. Re-test: `gpt-4.1` one-token call OK (10 tokens); pubmed 200, doi.org 301, crossref 302 reachable; jamanetwork.com 403 (publisher bot block, see DECISIONS #5).
- 01:00 Phase 0 started. Launched 3 discriminator-id drafting agents (cardio/volume; shock/renal/neuro; abdomen/fever/weakness) and 3 case-author agents (4 presentations each).
- 01:20 Case-author ×3 done: 36 base cases (108 inputs) written blind, validator 0 errors; committed 3d65e36.
- 01:30 Id drafts ×3 done (75/50/46) → merged 148 ids, 5 duplicates folded; committed b419c32.
- 01:35 Phase 2 deterministic modules + 30 tests (builder agent) committed 9516ecd.
- 01:45 Case-critic ×2 done: 20 pass / 16 revise. Revisions dispatched to the original authors (DECISIONS #11–15).
- 02:20 Author revisions ×3 applied (commit 09cc20b). Critic re-check: 26 pass / 10 fix → 11 exact edits applied by coordinator; validator 0 errors.
- 02:25 LLM modules (llm/parser/rank/pipeline/api) + 24 tests landed (54 total, all green); live startup_check → gpt-4.1. Commit 8bff84c.
- 02:30 PHASE0_GATE.md generated; owner gate opened. Phase 1 cardiology extraction starting in background.
- 03:40 Owner gate rulings received (DECISIONS #18); vocab cross-listings, 5 palpitations ids, compound splits, chest_pain_002 re-branch applied. Critic split re-check running.
- 03:45 Wave 1 (24 ids) + wave 2 (34 ids) extraction complete: 116 packets, validator 0 errors; status 72 quantified / 38 partial / 6 not_quantified; diff: 2 agree, 42 partial, 14 disagree. Red-team wave 1 running. verify_ui.py built (9 tests). Wave 3 (37 ids: shock/renal/neuro/abdomen/AMS + 2 palpitations) launched.
- 02:10 Rate limit killed 12 background agents (critic re-check, red-team ×2, eval builder, wave-3 extractors ×8). Critic's report had already been written to disk; agents resumed after reset (A-side extractors first to cap concurrency).
- 02:24 **Freeze #1**: content commit 39a698e; hash stamped into all 36 case files; freeze guard test added (37 tests). Benchmark is read-only from here except `reference_targets_mapped` at freeze #2.
- 02:55 Wave 3 complete: 190 packets over all 95 priority-1 ids. Red-team wave 1 committed (no fabricated numbers; direction/range/author/composite issues → prompt hardened, DECISIONS #23). Verification queue handed to owner (gate 2). Eval harness landed (155 tests). Wave 4 A-side (58 P2/P3 ids) + red-team wave 3 launched.
- 03:10 Red-team wave 2 committed (0 fabrication, 110/110 quotes verified). Sidecar + target map landed. **Freeze #2** = 28a5f2617dcd474602491e71823338316f18bc2d.
- 03:40 Freeze #2 (28a5f26). Arm C (generic LLM, gpt-4.1) run on all 108 frozen inputs as a DEV run (not the reportable run): 102/108 completed before the client had 429 backoff; preliminary, non-abstract signal: ~28 items per answer, bedside share ≈0.60, ~22% of items carry a numeric claim. Parser dry-run exposed out-of-vocab tags → corrective re-parse added (DECISIONS #27). Red-team wave 3 committed. Wave 4 A-side complete (58 ids); B-side running.
- 04:20 **Extraction complete**: 306 packets = 153 ids × 2 independent extractors; validator 0 errors. Red-team waves 1–3 committed; wave 4 launching. Parser: vocab corrective re-parse (108/108 parse) and `underspecified` flag to gate ask-first (DECISIONS #27, #29). Dev arm C run complete (108/108).
- 04:50 Red-team wave 4 complete (all 4 waves now committed; 153/153 ids reviewed). Code-review audit: 10/10 non-negotiables PASS with adversarial checks executed. Parser ask-first recalibrated (4/6 sensitivity, 0 false positives). PROGNOSTIC-unlabelled check added to the diff tool. Phase 1 extraction closed; owner verification is the critical path.
