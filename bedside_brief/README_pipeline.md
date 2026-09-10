# Bedside Brief pipeline (Phase 2)

```
one-liner ──► parser.py ──► retrieve.py ──► rank.py ──► render.py ──► validate.py ──► card (HTML)
              (LLM, vocab)  (SQLite, det.) (LLM, ids)  (stored     (numbers must     api.py: GET /
                                                        fields)     be in record)    POST /brief
                                                                                      GET /record/{id}
```
`pipeline.brief()` runs the five stages in order and returns `{parsed, candidates, chosen, card, validation}`.
`llm.LLMClient` is the only module that talks to a provider; `llm.FakeLLM` keeps every test offline.

## Where each non-negotiable (CLAUDE.md) is enforced

| Non-negotiable | Enforced at |
|---|---|
| LLM never emits sens/spec/LR/citations | `parser.py:system_prompt` and `rank.py:system_prompt` forbid it; `parser.py:parse_oneliner` and `rank.py:rank` pass every LLM string through `render.strip_numbers`; `rank.py:candidate_summary` sends only id/title/type/changes_what/badge, digit-stripped, and `rank.py:_assert_no_numbers` raises `RankerNumberLeak` if any literal survives. The ranker schema (`rank.py:RANK_SCHEMA`) has no numeric field; the parser schema's only number is `weight`. |
| Cards render only from stored fields of `verified` records | `retrieve.py:retrieve` (tier filter), `render.py:render_card` (skips non-verified), `pipeline.py:brief` builds `records_by_id` from the retrieved candidates only. |
| Validator blocks any number not in a linked verified record | `validate.py:validate_card` / `validate_or_block`, called last in `pipeline.py:brief`; blocked items are withheld, never re-generated. |
| Parser emits only vocab strings | `parser.py:_check_vocab` raises `ParserVocabError` (never drops); `_normalise_differentials` clamps, dedupes, sorts, truncates to `MAX_DIFFERENTIALS`. |
| Ranker chooses from candidate ids only, under limits | `rank.py:rank` raises `RankerContainmentError` for foreign ids or type/section mismatch; truncates to `MAX_ASK/MAX_EXAMINE/MAX_POCUS` in LLM order; drops `pocus` unless `POCUS_ENABLED`. |
| Underspecified input → "ask first", not a guess | `parser.py` asks for `missing_features`; `render.py:render_card` surfaces them as `ask_first`; `api.py:post_brief` returns a "Withheld" card (HTTP 502) on any parser/ranker contract failure. |
| Keys never printed or logged | `llm.py:LLMClient._sdk` reads `config.openai_api_key()` once; logs carry only model, token usage, latency. |
| Same provider/model for parser and ranker | one `LLMClient` instance per app (`api.py:lifespan`), resolved by `llm.py:startup_check` with fallback to `LLM_FALLBACK_MODEL`. |
| Audit link per item | `render.py:render_item` (`/record/{id}`) → `api.py:get_record`, 404 unless tier is `verified`. |

## Run
```
uvicorn bedside_brief.api:app        # GET /health shows resolved model + record counts
python3 -m pytest -q                 # offline; FakeLLM only
```
