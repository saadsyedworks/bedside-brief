# RETROSPECTIVE — Bedside Brief

Written 2026-09-12, at the pause (see `PLAN.md` STATUS banner and `DECISIONS.md` #63).
Three weeks of work, from kickoff to a finished abstract that was deliberately not
submitted. This is the record of what the exercise taught, including the mistakes,
so that whoever picks this up — most likely the author, later — does not re-learn it.

## The state this is written from

| | |
|---|---|
| Verified records | 153 (dual-extracted, quoted, page-located, each read by the author before promotion) |
| Not quantified | 24.2% — a legitimate state, never a manufactured number |
| Benchmark | 36 base cases → 108 inputs, authored blind and frozen before any library query |
| Eval | 3 arms × 5 runs; 427 owner-graded items; error analysis on 88 missed targets |
| Product code | ~1,400 lines (`bedside_brief/`) |
| Everything else | ~10,600 lines (eval harness, verification + judging tooling, tests) |
| Tests | 237 green |
| Abstract | 400 words, every number traced to a run file, never signed off |

---

## 1. The definition of done decided what got built

`CLAUDE.md` specified a tool **plus its technical validation, for an abstract due
Sept 15**. Nobody ever decided "build mostly apparatus." It followed anyway: the
product is 1,400 lines and the machinery for proving things about it is 10,600.

Every local decision was defensible. The aggregate produced a validated prototype
rather than a tool anyone would adopt — which is exactly what the stated deliverable
asked for.

**The lesson.** Whatever artifact is named as "done" is what gets built. "Every number
traced to a file" produces a traceable abstract. "Someone other than me used this on a
real patient" would have produced a different repository — probably with a worse
abstract and a better tool. That fork was chosen on day one, in a single sentence, and
was invisible until the finished thing didn't match what the author had pictured.

## 2. The publication ceiling was fixed before any code was written

`CLAUDE.md` assigned one person as "sole author, sole clinical verifier, sole judge."
That made the work fast: no coordination, no scheduling, 153 records verified in one
~6-hour sitting. It also made the primary outcome a self-assessment, which is the one
flaw no later engineering could repair.

Real effort went into blinding — item order hashed within a case so the arms interleave,
arm labels held only in a `judging_key.json` the judging page never received, a separate
re-grade sheet where only changes are ticked. All of it sound, all of it beside the
point, because the same person still authored the cases and graded the outputs.

**The lesson.** When a role assignment has one person both generating and grading, the
ceiling is set at kickoff. That is the moment to notice it — not at abstract time.

## 3. A metric can be a design property wearing a result's clothes

Arm A's bedside share is near-total **by construction**: arm A can only emit bedside
items. Reporting it as a finding would have been circular. Worse, this agent nearly
advised making *judged relevance* depend on bedside-ness, which would have imported the
same circularity straight into the primary outcome. The author's own instinct while
grading — "labs and ECGs are irrelevant, this is a bedside card" — was the same trap
approached from the other side.

The abstract ended up stating it as a design property, which is the honest form.

**The check that catches it.** Before reporting a number, ask what values it could
possibly have taken. If the answer is "only this one," it describes the design rather
than measuring it.

## 4. Validation is worth exactly what its negative controls are worth

Two bugs make the point, and they share a shape.

- `tools/validate.py`'s empty-estimate check tested a stat **dict**, which is truthy
  even when its value is null. It had never worked, while reporting clean.
- The judging page read `DocumentSnapshot.data` as a property when the runtime contract
  defines it as a function. The test stub written for it mirrored the same
  misunderstanding, so the test passed while the code was broken.

A test written from the same mental model as the code tests the model, not the code.
What breaks that loop is reading the contract instead of recalling it, and asserting
that checks **fail** on deliberately broken input rather than only that they pass on
good input. (Demonstrated the same day in a sibling project: four sabotage cases —
scrambled channel order, corrupted label prevalence, a truncated file, a dropped array
axis — were the only reason to believe its integrity checks fired at all.)

## 5. "Already done" must mean "done successfully"

The resume path in `eval/arms.py` returned stored failures as completed work. Seventeen
arm-A cases would have entered the metrics as genuine **empty cards** — 15.7% of the
arm, concentrated in two presentations.

That is a wrong number in a submitted abstract, produced by an optimisation for
restartability. Any resume/caching layer needs to distinguish a cached success from a
cached failure, and a regression test that fails without the distinction.

## 6. Mechanism analysis beat intuition, twice

**Library expansion.** Asked whether simply adding more records would close the recall
gap, the obvious answer was yes. The error analysis said otherwise: of 88 missed
must-have targets, 25% had no record, 25% were never offered by retrieval, and 50% lost
the 8-slot ranking competition. The intuitive fix addressed a quarter of the problem,
and this agent's initial advice was revised downward on the evidence.

**Safety cost.** The contraindication behaviour looked intrinsically expensive — adding
it dropped recall to 67.7% and perturbation responsiveness to 57.9%. The 2×2+1 ablation
showed the cost came from applying the caveat to all ~23 candidates, not from the
behaviour itself. A narrow deterministic gate keyed on patient state
(`bedside_brief/patient.py`) reached **zero** violations at 70.0% recall.

**The lesson.** "Safer everywhere" is frequently just noisier. Safety mechanisms have a
precision dimension, and measuring it is cheap compared to paying for it.

## 7. What the eval actually found

Stratified must-have recall is the most informative result in the project:

| | Arm A | Arm C (unconstrained) |
|---|---|---|
| Overall | 70.0% | 71.3% |
| Where the library holds a record | 72.2% | 72.6% |
| Where it holds none | 18.5% | 63.0% |

The architecture is not worse at recommending — it is **bounded by its library**, and it
ties where the library reaches. That reframes the recall "gap" from an architectural
deficit to a coverage fact, and it is the kind of claim that only a pre-frozen benchmark
can support.

The durable finding is the containment result: **0.0% versus 88.6%** unsupported numeric
claims. That is not a better model; it is a model structurally forbidden from emitting a
number, with deterministic code checking every card against linked verified records. It
is the one claim in the project requiring no trust in the author's judgement — and
therefore the part most worth keeping.

## 8. What this agent got wrong

**The judging page: four rounds on the wrong layer.** The author reported that the
buttons did nothing. Diagnoses offered, in order: silent exception handlers, a 12-read
startup burst, load ordering — the third introducing a regression of its own. The actual
cause was that the "not an item" button had no pressed-state CSS, rendering white-on-white
in light mode and 1.06:1 in dark. The tests asserted `aria-pressed`, which was correct
the entire time.

*An assertion about the DOM is not an assertion about what a person sees.* The
instrumentation that found it in one tap belonged in round one. When a user's report and
passing tests disagree, the tests are measuring the wrong layer — that is information,
not noise.

**Claiming state from proxies.** Reported "108/108, zero errors" from reading a log
rather than the output files. Reported a run as still going for ~50 minutes after it had
finished, because the process check was matching its own polling shells. Both were
self-corrected, but the pattern is asserting a state from a convenient signal instead of
the thing itself. The severe version came later: an entire session's work resumed in the
wrong repository, because the working directory disagreed with the handover summary and
the agent took the convenient reading instead of resolving the contradiction.

**Optimising inside a frame that was being questioned.** Asked whether the abstract fit
the venue, the agent proposed translating it into clinical English. The author's reply
was correct: a methods paper in clinical English is still a methods paper. The frame, not
the prose, was the thing in question.

## 9. What held up

- **The freeze protocol.** Hashes written into every case file, byte-identity enforced by
  `tests/test_freeze.py`. Targets could never be quietly retro-fitted to whatever the
  library happened to contain, which is the only reason the recall numbers mean anything.
- **Human gates on promotion.** No record reached `verified` without being read. The
  author excluded 9 estimates and corrected 1 value during verification, and later
  approved 9 red-team fixes individually rather than accepting a blanket packet flip —
  which would have discarded good estimates in 4 of the 9 cases.
- **Disclosure discipline.** The abstract discloses its own departures from
  pre-specification, unprompted: a rule calibrated on frozen inputs, and a rubric change
  that landed mid-grading and forced a scoped re-grade (44 rows re-issued, 29 changed).
  Nothing was quietly absorbed.
- **Fixes traced into the data.** Every owner-approved change is stamped into the
  record's `verification_notes` as an `[owner fix]` line. The two fabricated citation
  strings survive only there, as the audit trail.

## 10. Stopping was the highest-value judgement

The author reviewed a finished, audited, internally honest abstract and declined to
submit it — for reasons unrelated to its quality: it is a methods validation, and the
venue is a bedside clinical-skills meeting.

That judgement was available at any point in the preceding three weeks. The worry that
prompted it (an ~$800 registration) turned out to be mechanically moot — submission is
free and separate from registration, so the money decision would have come after
acceptance — and the answer was still no. Good decisions survive having their weaker
reasons removed.

**The lesson that generalises.** "Is this the right deliverable?" does not get asked by
momentum. It has to be scheduled, the way the owner gates were. Five gates were defined
at kickoff, and every one of them asked *is this work correct?* None of them asked *is
this work worth doing?*

---

## If this is picked up again

`PLAN.md` carries the resume order. Its short form: deploy it and use it yourself on real
admissions; then get one clinician who is not the author to use it; then run the resident
study (exam plan with versus without the brief). The first is small in code — an access
gate, a rate limit, a no-PHI disclaimer, a host — and the second is the one that lifts
the ceiling described in §2.

The methods work as it stands is submittable unchanged to a diagnostic-error or
informatics venue, where its strongest claim is the one that audience cares about.
