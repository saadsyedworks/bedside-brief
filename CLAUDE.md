# Bedside Brief — Claude Code project instructions

You are building Bedside Brief: an evidence-grounded AI pre-encounter bedside decision-support tool, plus its technical validation, for a conference abstract due **Tue 2026-09-15** and a poster on **2026-11-13**. Read `DAY1_FREEZE.md`, `discriminator_schema.json`, `extraction_packet_spec.md`, `benchmark_case_template.json`, `evaluation_rubric.md`, and `vocab.json` before doing anything. `PLAN.md` is your task list; work it top to bottom and keep it updated.

## Roles
- **Owner (Saad)**: sole author, sole clinical verifier, sole judge for relevance/safety. Only the owner promotes a record to `verified`. Only the owner edits `vocab.json` after Phase 0 sign-off. Only the owner signs off the abstract.
- **You**: author everything else — vocab draft, discriminator ID list, benchmark cases, extraction packets (via subagents), all code, tests, eval harness, figures, abstract draft. Review your own work with subagents before surfacing anything to the owner.

## Operating mode: autonomous by default
Work through `PLAN.md` without asking. Batch questions. Surface to the owner ONLY the items in "Owner gates" below. Everything else: decide, document the decision in `DECISIONS.md` with a one-line rationale, and move on. If uncertain between two reasonable options, pick the one that is simpler and more auditable.

## Owner gates (the only reasons to stop and ask)
1. **Phase 0 sign-off**: vocab + discriminator ID list + benchmark cases drafted → owner reviews/edits once (≈30–60 min). Then freeze #1.
2. **Verification queue**: records ready for owner verification, presented in a diff view (two packets side by side, disagreements first). Owner promotes or rejects. Never promote yourself.
3. **Judging queue**: blinded item list for relevance/safety scoring.
4. **Abstract sign-off**: draft + figure + every number traced to a harness output file.
5. **POCUS**: extract POCUS records but keep `pocus` type disabled in retrieval until the owner enables it in `DAY1_FREEZE.md`.
6. Anything that would change a frozen artifact (benchmark, vocab) — ask; never do.

## Non-negotiables (from the brief; enforce in code, not by intention)
- The LLM never emits sensitivity, specificity, LRs, or citations. Cards render only from stored fields of `verified` records. The validator blocks any card containing a number not present in a linked verified record.
- Two independent extraction packets per record; stored separately; diffed.
- Benchmark cases and free-text targets are authored **before** any library query, committed, hash recorded. After freeze #2 they are read-only.
- Abstract numbers run on the `verified` subset only. Report "N verified of M extracted."
- Multiple estimates per record when performance differs by population. Never average across populations.
- `not_quantified` is a legitimate state; do not manufacture numbers to avoid it.
- Retrieval is keyed on `differentials` (primary) and `indication_tags` (secondary); `presentations` is a filter.
- Underspecified input → "ask first" line, not a guess.

## Stack
Python 3.11+, FastAPI, SQLite (records + benchmark + runs), Jinja2 single-page UI (no chat transcript), pytest. LLM provider is configurable via `config.py` (`LLM_PROVIDER`, `LLM_MODEL`); default `openai` with `gpt-4.1` — or whichever current OpenAI model the owner's key can access; check with a one-token test call at startup and fall back to `gpt-4o` if needed. Keys come only from `.env` (`OPENAI_API_KEY`, optionally `ANTHROPIC_API_KEY`); `.env` is gitignored from the first commit and never printed or logged. Same provider/model for parser, ranker, and comparator arm C. Deterministic code for retrieval, render, validator, metrics. Keep it small; no frameworks beyond these.

## Repo layout
```
records/extracted/{id}__{agent}.json   # two per id
records/verified/{id}.json             # owner-promoted only
benchmark/cases/*.json                  # frozen after commit
bedside_brief/ (parser, retrieve, rank, render, validate, store, api)
eval/ (arms, metrics, judging_export, report)
agents/ (subagent prompts)
tests/
DECISIONS.md, PLAN.md, RUNLOG.md
```

## Subagent usage
- **extractor-A / extractor-B**: independent runs of `agents/extractor.md` per record id; different seeds/phrasing; never share outputs.
- **red-team**: reviews every batch of extraction packets for the failure modes in `agents/redteam.md`; flags, does not fix.
- **case-author**: drafts benchmark cases from `agents/case_author.md`; a second pass with **case-critic** checks clinical realism and that perturbation pairs change exactly one meaningful feature.
- **code-reviewer**: reviews each module against the non-negotiables before merge.

## Definition of done for Tuesday
Working prototype; ≥60 verified records (target 80–120); frozen benchmark (≥3 base cases/presentation with perturbation + noise variants); harness runs arms A/B/C and exports metrics + error analysis; one figure (bedside share A vs C); 400-word abstract draft with every number traced. If by Sunday night verified < 60 or end-to-end fails, switch to the fallback development abstract (see `PLAN.md`) and tell the owner.
