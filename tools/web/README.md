# Published pages

Source for the two web pages published as Claude artifacts. They are kept here so the pages are
reproducible from the repo rather than living only in a chat session.

| File | Published at | What it is |
|---|---|---|
| `ipad_verify.html` | artifact `c6df8fe3-0bc8-4447-b028-5a6e7d23f2b7` | The iPad verifier. Reads `meta/index` and `records/{id}` from the artifact's store and writes one doc per decision to `decisions/{id}`. |

### The decision document

```json
{"id": "exam_x", "action": "promote", "base": "A", "exclude": [1],
 "edits": {"A:0": {"lr_positive": 7.2, "note": "LR+ is 7.2 in Table 3"}},
 "notes": "Checked Table 3 directly.", "at": "2026-09-11T02:00:00Z"}
```

`exclude` drops estimates by their index in the chosen packet. `edits` corrects a stored value:
`pull_decisions.py` writes the new number, clears the confidence interval (it no longer describes that
estimate), records every change in `verification_notes`, and warns when a corrected value no longer
appears in its own quote. Corrections for the packet that was not promoted are discarded.
| `verification_queue.html` | artifact `99b0d712-64fc-4e35-97cc-bb67c629a9f4` | The static owner briefing: where to start, the agreement split, the judgement calls. |

## Rebuilding the verifier's data

```bash
python3 tools/seed_ipad.py <out_dir>     # one JSON per id + _index.json, in queue order
# then upload out_dir/_index.json to meta/index and each {id}.json to records/{id}
```

Re-run the seed after any change to `records/extracted/`, `records/redteam/`, or `discriminator_ids.json`.

## Pulling decisions back

```bash
# read the decisions collection into a directory, then:
python3 tools/pull_decisions.py <decisions_dir> --dry-run
python3 tools/pull_decisions.py <decisions_dir>
```

Each `promote` rebuilds the chosen packet minus excluded estimates, remaps `source_index`, stamps
`tier`/`verified_by`/`verified_at`/`verification_notes`, and is written only if it passes the same
schema, vocabulary and unit checks the desktop app enforces.

## Testing the page before publishing

`tools/web/check_ipad_page.py` drives the page in headless Chromium with a stubbed store: it asserts
the queue renders, a record opens with both packets, and a promote writes the expected decision.
Run it after any edit to `ipad_verify.html` — a JavaScript syntax error otherwise leaves the page
stuck on its loading line with nothing in the UI to say why.

```bash
pip install playwright
python3 tools/web/check_ipad_page.py <seed_dir>
```
