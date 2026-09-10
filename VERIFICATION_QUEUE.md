# Owner gate 2 — verification queue

Phase 1 is complete: **153 discriminators × 2 independent extraction packets = 306 files**, every one
schema- and vocab-valid. Four red-team waves reviewed all 153 ids. **No fabricated number was found in
any wave.** Nothing renders and nothing enters the evaluation until you promote it here.

## Start the app

```bash
git clone https://github.com/saadsyedworks/bedside-brief
cd bedside-brief
git checkout claude/git-repo-setup-rvdx9z
./start_verify.sh                   # opens http://127.0.0.1:8765
```

`start_verify.sh` creates a local virtualenv on first run, installs the dependencies, starts the app and
opens it in your browser. Pass a port if 8765 is taken: `./start_verify.sh 8899`.

If something goes wrong:

| Symptom | Fix |
|---|---|
| `externally-managed-environment` from pip | You ran `pip install` directly. Use `./start_verify.sh`, which installs inside `.venv`. |
| `permission denied: ./start_verify.sh` | `chmod +x start_verify.sh`, or run `bash start_verify.sh`. |
| `No module named venv` (Debian/Ubuntu) | `sudo apt install python3-venv`, then rerun. |
| Nothing opens, no error | The server is running; open <http://127.0.0.1:8765> yourself. The script never opens a browser on Windows. |
| Windows | Use Git Bash or WSL, or run the four steps by hand with `py -m venv .venv` and `.venv\Scripts\python tools/verify_ui.py`. |

Packets A and B sit side by side, differences highlighted, each estimate linked to PubMed or DOI, with
the red-team flags for that id at the top. `p` promotes, `r` rejects with a reason, `n` skips. Promotion
re-checks schema, vocabulary, units, and quote-plus-location before anything is written, and only ever
writes `records/verified/`. Commit and push that folder whenever you stop.

## Verifying from an iPad

There is a web verifier that needs no terminal at all:
**https://claude.ai/code/artifact/c6df8fe3-0bc8-4447-b028-5a6e7d23f2b7**

Both packets sit side by side (stacked in portrait), every estimate shows its quote, its location and a
tappable PubMed or DOI link, and the red-team flags for that record sit at the top. Tap **Promote A**,
**Promote B**, **Reject** or **Skip**; exclude any estimate you don't want carried over before you
promote. Decisions save to the page's own store and it advances to the next undecided record.

When you have a batch done, tell me and I pull them into the repo with `tools/pull_decisions.py`,
which rebuilds each record from the packet you chose, drops the estimates you excluded, stamps
`verified_by` and `verified_at`, and refuses anything that fails schema, vocabulary or units. The
desktop app stays the fuller tool: it lets you edit any field, the iPad page is choose-and-exclude.

You can also run the desktop app on a computer and browse it from the iPad on the same Wi-Fi:
`./start_verify.sh` won't do it, so run `python3 tools/verify_ui.py --host 0.0.0.0`, then open
`http://<that computer's IP>:8765`. The queue has no login, so only do that on a network you trust.

## Start here: six cheapest upgrades

For each of these, one packet says `not_quantified` while the other carries a real, located, verified
number. Promote from the packet that found it. Six records for a few minutes of work.

| id | promote from | what the other packet missed |
|---|---|---|
| `exam_chest_hyperresonance` | A | Oshaug 2013 Table 3/4 (COPD LR+ 9.5) |
| `exam_kussmaul_sign` | A | Dubé 2021 meta-analysis, RV infarction |
| `exam_line_exit_site_erythema_purulence` | A | Cobo-Sánchez 2024 exit-site scale |
| `hx_steroid_exposure_withdrawal` | B | Ross & Levitt 2013 hyperpigmentation |
| `hx_recent_antibiotics_new_diarrhea` | B | Katz 1996 (note the 30-day vs 8–12-week window) |
| `exam_tense_distended_abdomen_iah` | A | Sugrue 2002 (B mis-recalled the journal and gave up) |

## Then work the queue in its own order

`records/diff_report.md` orders it: fabrication suspects and numeric mismatches first, then RCE-backed
agreements, then the rest. Current state across 153 ids: 26 agree, 93 partial, 34 disagree. "Partial"
usually means the two extractors chose different populations or sources rather than conflicting numbers.

## Four things only you can settle

1. **Units.** Sensitivity and specificity are stored as proportions (0.82, never 82). The tooling enforces this.
2. **Direction.** `lr_positive` means the finding is present, `lr_negative` means absent. A few packets
   inverted this where the source reported the negative sign; fix it in the draft.
3. **Composites.** An estimate for "JVD at rest or inducible" is not an estimate for JVP alone. Either drop
   it or keep the `COMPOSITE:` prefix so the card says so.
4. **Empty estimates.** Five rows carry no numeric field at all (kappa or prevalence only). Delete the row
   and keep the text in the notes.

## One question batched for you

`exam_ascites_flank_dullness_fluid_wave` and `exam_shifting_dullness` share a single evidence base; both
extractors flagged it independently. Proposal: fold into `exam_shifting_dullness` with fluid wave and flank
dullness as separate `estimates[]` rows. The id list is gate-approved, so I have not touched it.

## What 60 verified records buys

The abstract's comparison numbers run on the verified subset only, reported as "N verified of M extracted".
Below 60 by Sunday night, PLAN.md switches to the development abstract: architecture, store statistics and
the frozen benchmark, with no comparison numbers. Everything else is already built and tested, so
verification is the only thing on the critical path.
