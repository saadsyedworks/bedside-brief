# Bedside Brief — code review (continuation of a usage-limit-interrupted audit)

Reviewed: `CLAUDE.md`, `DAY1_FREEZE.md`, `evaluation_rubric.md`, `DECISIONS.md` (all, with focus on
#10, #16, #24, #27, #29, #30, #32), `bedside_brief/README_pipeline.md`, all of `bedside_brief/*.py`,
`eval/*.py`, `tools/verify_ui.py`, `tools/validate.py`, and `tests/`.

## 0. Prior fixes (DECISIONS #32) — re-verified, hold

| Fix | Where | Verified |
|---|---|---|
| `_SKIP_KEYS` excludes `extraction_notes`/`verification_notes` | `bedside_brief/store.py:_SKIP_KEYS`, `numbers_in_record` | Confirmed by direct call: a record with `extraction_notes="OR 42.7..."` / `verification_notes="OR 99.9..."` does **not** get those numbers into `numbers_in_record()`. Added regression test `tests/test_store.py:test_notes_fields_never_widen_the_number_allow_list`. |
| `block()` strips violating card-level fields | `bedside_brief/validate.py:block` | Confirmed: `ask_first` containing a foreign number is removed from the blocked card, which then re-validates clean. Added regression test `tests/test_validate.py:test_block_strips_violating_card_level_fields`. |
| `tests/test_freeze.py` byte-identical guard vs freeze #2 | `tests/test_freeze.py:test_case_is_byte_identical_to_freeze2` | Present, compares full JSON (not just the freeze-#1 stripped comparison) against commit `28a5f2617dcd474602491e71823338316f18bc2d`, parametrized over all 36 case files. Passing. |

No production code needed further changes for these three; only test coverage was added (see §6).

## 1. LLM never emits numbers reaching the card — **PASS**

Enforced in three independent layers: (i) parser/ranker schemas carry no free numeric field except
the parser's `weight` (`parser.py:PARSER_SCHEMA`, `rank.py:RANK_SCHEMA`); (ii) every LLM-origin
string is passed through `render.strip_numbers` at its origin — `parser.py:parse_oneliner`
(`chief_complaint`, `time_course`, `modifiers`, `missing_features`) and `rank.py:rank`
(`rationale`), plus again defensively in `render.render_item`; (iii) `validate.validate_card` is
the last-mile numeric check against the linked verified record.

Ran four throwaway adversarial scripts under the scratchpad (not committed) against a synthetic
verified/extracted store built from `tests/conftest.py` fixtures:

- **(a)** FakeLLM ranker rationale `"LR+ 12.3 (95% CI 8-16), sensitivity 91%, PMID 1234567, DOI
  10.1001/jama.999.888"` — every digit was replaced with `[n]` before the item reached
  `render_card`; the validator found zero violations (there was nothing left to violate). PASS.
- **(b)** FakeLLM ranker chosen an id that exists only in `records/extracted/`
  (`hx_positional_vertigo`, tier `extracted`) — `retrieve.py` never surfaces it as a candidate
  (tier filter at retrieval), so `rank.py:rank` raised `RankerContainmentError` before any card was
  built. PASS.
- **(c)** `GET /record/{id}` for that same extracted-tier id → HTTP 404 (`api.py:get_record`'s
  `record.get("tier") not in config.RENDER_TIERS` check); the verified counterpart → 200. PASS.
- **(d)** One-liner echo, `chief_complaint`, `time_course`, `modifiers`, HTML chrome: `render_card`
  never even puts `time_course`/`modifiers` on the card object; `chief_complaint` is stripped at
  the parser. The only digits found outside the evidence `<details>` blocks in the rendered page
  were `charset="utf-8"` (markup) and the **user's own typed one-liner** echoed back into the
  input box (trusted user input, not LLM output — expected and correctly autoescaped by Jinja2).
  No LLM-origin digit reached page chrome. PASS.

## 2. Two independent packets, diffed; verify_ui write-scope — **PASS**

`tools/verify_ui.py` reads `records/extracted/*__*.json` (two packets per id, agent suffix in the
filename) and never writes into that directory. Writes are confined to:
- `records/verified/{id}.json` (`promote_record`) — stamps tier/verified_by/verified_at, validates
  via `bedside_brief.store.record_problems` + `tools/verify_ui.py:extra_record_checks`, writes, then
  **re-validates the saved file** through `tools.validate.validate_records` and rolls back
  (restores the previous file or deletes it) if that finds a problem — belt-and-braces.
- `records/rejected/{id}.json` (`reject`) and `records/drafts/{id}.json` (`save_draft`).

`grep`ed the whole repo for any other writer of `RECORDS_VERIFIED`/`records/verified`:
`eval/run_all.py:build_smoke_store` is the only other reference, and it monkeypatches
`config.RECORDS_VERIFIED` to a **synthetic path under the run dir** only for the duration of
`store.build_index`, restored in a `finally`. It never touches the real `records/verified`. No
other module writes there.

## 3. Benchmark read-only after freeze; `--allow-unfrozen` scope — **PASS**

`eval/cases.py`, `eval/mapping.py`, and `eval/arms.py` only ever read `benchmark/cases/*.json` and
`benchmark/target_map.json` (grepped for every reference to `BENCHMARK_CASES`/`benchmark/cases` —
no writer). `eval/mapping.propose_mapping` explicitly documents "never touches git and never writes
benchmark/target_map.json itself" and only writes a `*.proposed.json` file under the run dir.
`tests/test_freeze.py` independently guards byte-identity against both freeze commits.

`--allow-unfrozen` only bypasses one thing: the `FreezeError` in `eval/cases.load_cases` that
otherwise refuses to run on a case file whose `frozen_commit` is empty. It does not disable the
freeze-#2 pytest guard, does not permit writes, and does not affect target mapping or metrics
logic. Scope matches its docstring.

## 4. Abstract numbers on verified subset, "N verified of M extracted" — **PASS**

`eval/metrics.py:compute_metrics` computes `store.verified = len(verified)` (records with
`tier == "verified"`) and `store.extracted = len(extracted_ids)` (distinct ids with ≥1 packet in
`records/extracted/`, passed in from `eval/run_all.py:extracted_ids()`), rendered in
`metrics_markdown` as "N verified" "of M extracted". `tools/number_audit.py:store_stats` uses the
identical definitions (`records/verified/*.json` file count; distinct extracted ids by
`stem.split("__",1)[0]`), and `Resolver.cross_checks()` MISMATCHes if a run's `metrics.json`
disagrees with the live tree. Definitions agree by construction and are cross-checked.

## 5. Multiple estimates never averaged/collapsed — **PASS**

`render.render_item` builds `"evidence": [_estimate_view(e, sources) for e in
record.get("estimates", [])]` — every estimate is rendered as its own block; no reduction.
Grepped `bedside_brief/*.py` for any averaging construct (`mean(`, `average`, `np.mean`,
`statistics.`, `sum(...)/`) — none found anywhere in the deterministic pipeline.

## 6. `not_quantified` first-class — **PASS**

- Render: `render_item`'s `evidence_badge` = `record["evidence_status"]`; the HTML template has a
  dedicated `.badge.not_quantified` style and an explicit "Not quantified... guideline or consensus
  based" line when an item has zero estimates.
- Retrieval: `retrieve.py` never filters on `evidence_status` — a `not_quantified` record is
  retrieved and ranked exactly like a `quantified` one.
- Metrics: `eval/metrics.py` reports `store.not_quantified` / `not_quantified_share`, and
  `target_recall_must_have.strata` breaks must-have recall out by `quantified` /
  `not_quantified` / `unmapped` (DECISIONS #18 ruling 3).

## 7. Retrieval semantics + determinism — **PASS**

Keyed on `differentials` (summed weights) primary, `indication_tags` secondary (`TAG_BOOST=0.25`);
`presentation` is a filter only — in-presentation candidates sort before cross-presentation ones
(`retrieve.retrieve`'s two lists), and each `Candidate.cross_presentation` flag survives into the
eval outputs. POCUS is excluded from `records_matching` results whenever
`pocus_enabled` is false (both in `retrieve()` and `retrieve_fixed_order()`).

Determinism: ran `retrieve.retrieve()` three times on an identical fixture/parsed-input triple —
byte-identical ordered id/score/cross_presentation tuples every time (no LLM, no randomness, sort
key `(-score, id)` is total).

## 8. Underspecified → "ask first", gated on the parser flag — **PASS**

`parser.py` contract requires `underspecified: bool`; `missing_features` is only populated (and
only 1–3 *history* questions) when true (enforced in the system prompt and in
`parse_oneliner`'s post-processing, which forces `missing_features=[]` whenever
`underspecified` is false). `render.render_card` gates `card["ask_first"]` on
`parsed.get("underspecified", True)` **and** a non-empty `missing_features` list — in production
`parsed` always comes from `parse_oneliner`, so the flag is always explicitly set; the `True`
default only matters for hand-built `parsed` dicts bypassing the parser (none exist in production
code paths). `eval/metrics.py:askf` compares `out.ask_first` (arms A/B: from the real
`render_card` gate; arm C: the `_C_ASK_FIRST` regex heuristic per DECISIONS #24) against
`case.underspecified_expected` — same flag, same semantics, consistently applied.

## 9. Secrets — **PASS**

- `grep -rn "sk-"` across `*.py/*.md/*.json` (excluding `.env`): zero real API-key-shaped
  literals — the only "sk-" substring hits are inside filenames like `exam_skew_deviation` (false
  positive on the search string itself).
- No logging of the key or an `Authorization` header anywhere: `bedside_brief/llm.py` reads
  `config.openai_api_key()` exactly once at SDK construction and its module docstring/comments
  state what is/isn't logged; the only things actually passed to `log.info`/`log.warning` in that
  file are model name, token usage, latency, and exception type names — never prompt/reply text or
  headers.
- `.env` is listed in `.gitignore` (`.env`, `.env.*`, with `!.env.example` carved out) and
  confirmed **not tracked** (`git ls-files` empty, `git check-ignore -v .env` matches
  `.gitignore:1`).
- `config.py` is the only place `OPENAI_API_KEY` is read.

## 10. Determinism — **PASS**

`config.LLM_TEMPERATURE = 0.0`, `config.LLM_SEED = 7`, both applied unconditionally in
`LLMClient._call` for every completion; one `LLMClient` instance is shared across parser, ranker
and arm C (`api.py:lifespan`, `eval/run_all.py`), so "same provider/model" and "same
temperature/seed" hold structurally, not by convention. `retrieve.py`, `render.py`, `validate.py`,
`eval/metrics.py`, `eval/classify.py`, `eval/item_parser.py` are all pure functions over their
inputs (verified by the determinism re-run in §7); `eval/item_parser.py`'s regexes are static
module-level compiled patterns with no randomness or external state.

## Also flagged (per the audit brief)

- **Swallowed exception with no log line** — `bedside_brief/store.py:23`:
  ```python
  try:  # canonical vocab sets live in tools/validate.py
      from tools.validate import DIFFERENTIALS, PRESENTATIONS, TAGS
  except Exception:  # pragma: no cover - fallback if tools/ is mid-edit by another agent
      ...
  ```
  This is a bare `except Exception` with **no logging at all**, unlike every other broad handler in
  the codebase (which at minimum `log.warning`s). If `tools/validate.py` ever has a real bug (not
  just "mid-edit"), this silently falls back to a second, independently-computed vocab set from
  `vocab.json` with zero visibility that the primary path failed. It does not currently cause a
  vocab mismatch (both paths compute `DIFFERENTIALS` identically from `vocab.json`), so it is not a
  non-negotiable violation today, but it is exactly the kind of masked failure the brief asked to
  flag. Suggested fix (not applied — not a confirmed violation): add `log.warning("tools.validate
  import failed (%s); falling back to vocab.json directly", exc)` in the except block.
- **No path renders a non-`verified` record onto a card**: confirmed triple-redundant —
  `retrieve.py` (candidate generation), `render.render_card` (render-time), `validate.validate_card`
  (post-render) all independently check `record.get("tier") not in config.RENDER_TIERS`, plus
  `api.get_record` for the audit-link endpoint. No gap found.
- **`render.strip_numbers` coverage of LLM-origin strings**: every LLM-origin string that can reach
  a card is covered — `chief_complaint`, `time_course`, `modifiers`, `missing_features`
  (`parser.py`) and `rationale` (`rank.py`, re-stripped again in `render.render_item`).
  `time_course`/`modifiers` are stripped at the parser even though `render_card` never places them
  on the card object at all (defense in depth). No LLM-origin string reaches the page unstripped.

## 6. Test suite / edits made

Added two regression tests (no production code changes were needed — both DECISIONS #32 fixes hold
as committed):
- `tests/test_store.py:test_notes_fields_never_widen_the_number_allow_list` — locks in that
  `extraction_notes`/`verification_notes` numbers never enter `numbers_in_record()`.
- `tests/test_validate.py:test_block_strips_violating_card_level_fields` — locks in that
  `validate.block()` removes a violating card-level field (e.g. `ask_first`) and the result
  re-validates clean.

```
python3 -m pytest -q
204 passed, 1 warning in 2.73s
```
(was 202 before these two additions; suite stays green.)

## Summary table

| # | Item | Verdict |
|---|---|---|
| 1 | LLM never emits sens/spec/LR/citations onto a card (incl. adversarial checks a–d) | PASS |
| 2 | Two independent packets, diffed; verify_ui write-scope; nothing else writes verified | PASS |
| 3 | Benchmark read-only after freeze; `--allow-unfrozen` scope | PASS |
| 4 | Abstract numbers on verified subset only, "N verified of M extracted" agreement | PASS |
| 5 | Multiple estimates never averaged/collapsed | PASS |
| 6 | `not_quantified` first-class (render/retrieval/metrics) | PASS |
| 7 | Retrieval semantics (differentials primary, tags secondary, presentation filter, POCUS gate, cross-presentation ordering) + determinism | PASS |
| 8 | Underspecified → ask-first gated on parser flag, consistent in eval | PASS |
| 9 | Secrets (no "sk-", no key/Authorization logging, `.env` gitignored, single reader) | PASS |
| 10 | Determinism (temperature 0, seed, pure deterministic modules, stable regexes) | PASS |
| — | Prior 3 fixes (DECISIONS #32) still hold | Confirmed, tests added |
| — | Swallowed exceptions that could mask a violation | 1 flagged (`store.py:23`, no log line) — not a non-negotiable violation, not fixed |
| — | Card rendering non-verified tier | No gap (triple-redundant checks) |
| — | `strip_numbers` coverage of LLM-origin strings | Complete |

No non-negotiable violations found beyond the three already fixed and re-verified above. All 204
tests pass.
