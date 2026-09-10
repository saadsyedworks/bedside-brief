# Bedside Brief

Evidence-grounded, pre-encounter bedside decision support for inpatient internal medicine, plus its
technical validation. One-liner in → a ~20-second card of what to **Ask**, **Examine** (and, when enabled,
**POCUS**) before seeing the patient. Every number on the card comes from a stored, owner-verified
record with a quote, a location, and a PubMed/DOI link. The language model never writes a number.

> Review. Pocket the phone. See the patient.

## How it works

```
one-liner ──LLM parser──▶ {presentation, differentials (vocab), tags, missing_features}
           ──deterministic retrieval──▶ verified records keyed on differentials, boosted by tags,
                                        filtered by presentation (POCUS excluded unless enabled)
           ──LLM ranker (ids only)───▶ ≤4 Ask · ≤4 Examine · ≤3 POCUS, from candidates only
           ──deterministic render────▶ card from stored fields; evidence drawer; audit link per item
           ──validator───────────────▶ blocks any number not present in a linked verified record
```

Where each non-negotiable is enforced in code: `bedside_brief/README_pipeline.md`.

## Repository layout

| Path | What |
|---|---|
| `DAY1_FREEZE.md`, `CLAUDE.md`, `PLAN.md` | Frozen scope, working rules, task list (kept current) |
| `vocab.json` | Controlled vocabulary: 12 presentations, differentials, indication tags (owner-edited only) |
| `discriminator_schema.json` | JSON Schema for every record |
| `discriminator_ids.json` | The extraction universe (153 bedside discriminators, PubMed-confirmed anchors) |
| `benchmark/cases/*.json` | Frozen benchmark: 36 base cases, each with one perturbation pair and one noise variant |
| `records/extracted/{id}__extractor-{A,B}.json` | Two independent extraction packets per id |
| `records/verified/{id}.json` | Owner-promoted records — the only tier that renders or is evaluated |
| `records/diff_report.md`, `records/redteam/` | Deterministic A/B diff and red-team reports |
| `bedside_brief/` | Pipeline: `store`, `parser`, `retrieve`, `rank`, `render`, `validate`, `bayes`, `pipeline`, `api` |
| `eval/` | Arms A/B/C, metrics, judging export/import, error analysis, report |
| `tools/` | `pubmed.py` (e-utils/Crossref), validators, id merge, extractor prompt, diff report, `verify_ui.py` |
| `agents/` | Subagent prompts: extractor, red-team, case author, case critic |
| `DECISIONS.md`, `RUNLOG.md` | Every non-owner decision with rationale; chronological log |

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add OPENAI_API_KEY; .env is gitignored and never logged
python3 -m pytest -q          # offline test suite (FakeLLM); includes the freeze guard
```

## Run the app

```bash
python3 -c "from bedside_brief.store import build_index; build_index()"   # index verified records
uvicorn bedside_brief.api:app --reload                                  # http://127.0.0.1:8000
```

`GET /health` reports the resolved model and record counts; `GET /record/{id}` is the audit link.

## Verify records (owner only)

```bash
python3 tools/verify_ui.py        # http://127.0.0.1:8765
```

Queue order comes from `records/diff_report.md` (disagreements and fabrication suspects first). Each
record shows packets A and B side by side with links to the cited source; **p** promotes (schema- and
vocab-checked, `tier: verified`, `verified_by`, `verified_at`), **r** rejects with a reason, **n** skips.

## Reproduce the extraction

```bash
python3 tools/extract_prompt.py A exam_jvp_elevated exam_s3_gallop   # prompt for extractor-A
python3 tools/validate.py records records/extracted                 # schema + vocab + quote/location rules
python3 tools/normalize_units.py records/extracted                  # sens/spec as proportions 0–1
python3 tools/diff_report.py --resolve > records/diff_report.md     # A/B diff with live PMID/DOI checks
```

Literature access is through NCBI e-utils, PMC open access, and Crossref only (`tools/pubmed.py`);
publisher sites are not used, so `location` is "Abstract, Results" unless PMC full text exists.

## Freeze protocol

1. **Freeze #1** — cases and free-text targets authored blind to the library, critic-reviewed, committed;
   the commit hash is stamped into every case file (`frozen_commit`). `tests/test_freeze.py` fails on drift.
2. **Freeze #2** — `reference_targets_mapped` filled from targets → record ids; committed; hash recorded in `DECISIONS.md`.
3. All arms run on the frozen set. Product fixes are allowed afterwards; the frozen set is re-run and both runs reported.

## Evaluation

```bash
python3 -m eval.run_all --smoke                 # 3 cases, FakeLLM, end-to-end in seconds
python3 -m eval.run_all --arms A,B,C            # full frozen set → eval/runs/<timestamp>/
python3 -m eval.judging_export --run-dir eval/runs/<timestamp>   # blinded CSV for owner scoring
python3 -m eval.report --run-dir eval/runs/<timestamp>           # tables + figure; numbers annotated with source paths
```

Metrics follow `evaluation_rubric.md`: bedside share (headline, A vs C), target recall (must-have, stratified
quantified vs not-quantified; all), library coverage, evidence fidelity, unsupported-claim rate, perturbation
responsiveness, noise stability, brevity, not-quantified share; sensitivity analyses with ECG as bedside and
medication review as off-bedside. Abstract numbers are computed on the verified subset only and reported as
"N verified of M extracted."

## Limitations (disclosed)

Single author and single clinical verifier. Synthetic benchmark. No bedside-time, real-patient accuracy,
outcome, or behaviour-change claims. POCUS records are extracted but disabled in retrieval by default.
