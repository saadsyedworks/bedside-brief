# DECISIONS — batched, one line each, newest at bottom

| # | Date | Decision | Rationale |
|---|------|----------|-----------|
| 1 | 2026-09-10 | LLM model = `gpt-4.1` (resolved `gpt-4.1-2025-04-14`), provider `openai`, verified with a one-token call at kickoff. | CLAUDE.md default; key has access. Fallback `gpt-4o` wired in config.py but not needed. |
| 2 | 2026-09-10 | Benchmark stored as ONE file per base case with `perturbation_pair` and `noise_variant` nested, i.e. 36 files = 108 cases. | Matches `benchmark_case_template.json` exactly; PLAN.md's "108 files" read as 108 cases. Eval harness expands each file into 3 inputs. |
| 3 | 2026-09-10 | Discriminator id prefixes fixed: `hx_` history, `exam_` exam, `fn_` functional, `pocus_` POCUS. | Satisfies schema pattern `^[a-z]+_[a-z0-9_]+$`; type is recoverable from id. |
| 4 | 2026-09-10 | `discriminator_ids.json` schema: `{"ids":[{id,title,type,presentations[],differentials[],indication_tags[],expected_evidence,anchor_source,priority}]}`; `priority` 1 = extract first. | PLAN.md lists the required fields; `anchor_source`/`priority` added so extractors and the cardiology-first batch order are explicit. |
| 5 | 2026-09-10 | Publisher full-text sites (jamanetwork.com) return 403 to the sandbox; extractors use PubMed/PMC/Europe PMC/Crossref for quotes and locations, and record `location` from abstract/PMC tables. | Bot-blocking on the publisher side; PubMed abstracts of RCE articles carry the pooled LRs. Owner verification uses the primary. |
| 6 | 2026-09-10 | POCUS: extracted, `pocus` type disabled in retrieval (`POCUS_ENABLED = False` in config.py) until owner flips DAY1_FREEZE.md. | Owner instruction at kickoff. |
| 7 | 2026-09-10 | Literature lookups use Bash `curl`/Python `urllib` against NCBI e-utils, PMC OA, and Crossref (all reachable after the Full switch); the WebFetch tool stays egress-blocked because its policy is fixed at session start. `tools/pubmed.py` wraps e-utils so every extractor uses the same auditable path. | Subagents verified reachable via shell; WebSearch works for discovery only. |
