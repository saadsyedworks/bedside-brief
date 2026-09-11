# Proposed fixes to the verified store — for owner approval

Status: **APPLIED** in commit `206658a` on 2026-09-11, after the owner approved
all four judgement calls (`flip-a`, `label`, `rewrite`, `apply`). The store went
from 153 records / 349 estimates to 153 records / 337 estimates; validator 0
errors, warnings 14 → 8; 204 tests green. Every change is stamped into the
record's `verification_notes` as an `[owner fix]` line, and `record_version` is
bumped, so each record says what was changed after promotion and why.

What follows is the proposal as it was put to the owner, kept as the record of
what was decided and on what evidence. The two classes below describe how each
fix would have been made; both were applied by `tools/apply_fixes.py`, which
remains a dry run by default and is idempotent — re-running it now reports no
further change.

Two classes of fix:

- **Class A — you can do these yourself in the iPad verifier.** They are
  estimate exclusions and numeric corrections, which the verifier already
  expresses. Re-open just the listed records, exclude the listed estimates, and
  re-run `python3 tools/pull_decisions.py`.
- **Class B — the verifier cannot express these.** Citation strings, prose in
  `interpretation`, adding a source, adding an estimate. If you approve, I apply
  them as a commit; the diff for each is written out below.

---

## Summary

| # | Record | Defect | Class | Recommendation |
|---|---|---|---|---|
| 1 | `exam_carotid_upstroke_delayed` | LR+ 2.8 is the bottom of a range 2.8–130 | A | delete estimate [1] |
| 2 | `exam_chest_wall_tenderness_reproducible` | LR+ 0.2 is the bottom of a range 0.2–0.4 | A | delete estimate [2] |
| 3 | `exam_murmur_late_peaking_systolic` | LR+ 8.0 and LR− 0.05 are both range endpoints; no estimate left for the record's own finding | A + B | delete [0] and [1], add extractor-A's Shellenberger row |
| 4 | `exam_shock_index` | outcome rows not labelled `PROGNOSTIC:` | B | prefix [0] and [1] |
| 5 | `pocus_pericardial_effusion` | two rows use clinical tamponade as the reference standard | A | delete [2] and [3] |
| 6 | `pocus_bladder_volume` | **first author invented** ("Beacock CJ") + inverted target | B | fix citation; flip base packet to A |
| 7 | `exam_abdominal_rigidity_guarding` | **author list pasted from the wrong paper** | B | fix citation; label estimates pediatric |
| 8 | `fn_single_breath_count` | one row cited to a review table with "attribution ambiguous" | B | replace [2] with the traced primary (Kukulka 2020) |
| 9 | `hx_palpitations_before_syncope` | estimate (LR+ 0.74) contradicts the rule-in interpretation prose | B | keep the number, rewrite the prose |
| — | 6 records | estimates with no numeric value at all | A | delete 6 estimates; 3 records drop to `not_quantified` |

Two corrections to what I told you earlier:

- **Empty estimates: 6, not 11.** Five of the eleven were already dropped by your
  own exclusions during promotion.
- **"Flip to the other packet" is the wrong fix for 4 of the 9.** Flipping
  `exam_shock_index`, `pocus_pericardial_effusion`,
  `exam_chest_wall_tenderness_reproducible` and `exam_murmur_late_peaking_systolic`
  to extractor-A would throw away good estimates to remove one bad one. Deleting
  the single bad row is strictly better. Flipping is only right for
  `pocus_bladder_volume`.

One coherent root cause is worth noting: defects 1, 2 and 3 are all the *same
error against the same abstract*. Etchells 1997 (PMID 9032164) reports only
between-study ranges — "slow rate of rise of the carotid pulse (positive
likelihood ratio, 2.8-130)", "mid to late peak intensity of the murmur (positive
likelihood ratio, 8.0-101)", "absence of murmur radiation to the right carotid
artery (negative likelihood ratio, 0.05-0.10)". Extractor-B took the lower bound
of each as a point estimate. That is a single failure mode, not three.

---

## Class A — exclusions you can make in the verifier

### 1. `exam_carotid_upstroke_delayed` — delete estimate [1]

```
- [1] src=1 (Etchells 1997)  LR+ 2.8
-     quote: "a slow rate of rise of the carotid pulse (positive likelihood ratio, 2.8-130)"
```

2.8 is the lowest of six studies, not a pooled value. Rendered as-is the card
would say LR+ 2.8 for a finding whose pooled LR+ is 9.04.

**After:** one estimate — Shellenberger 2023 pooled, sens 0.57 / spec 0.94 /
LR+ 9.04 (3.12–25.44) / LR− 0.46. Identical to extractor-A's packet. Nothing is
lost. Keep Etchells 1997 in `sources` as context.

### 2. `exam_chest_wall_tenderness_reproducible` — delete estimate [2]

```
- [2] src=2 (Panju 1998 RCE)  LR+ 0.2
-     quote: "chest pain reproduced by palpation (LR range, 0.2-0.4)"
```

**After:** Bruyninckx pooled LR+ 0.23 and Goodacre LR+ 0.3 — two real point
estimates, both already in the record. Extractor-A read the same row as 0.3,
which is also a range endpoint, so deleting beats flipping.

### 3. `exam_murmur_late_peaking_systolic` — delete estimates [0] and [1]

```
- [0] src=0 (Etchells 1997)  LR+ 8.0
-     quote: "mid to late peak intensity of the murmur (positive likelihood ratio, 8.0-101)"
- [1] src=0 (Etchells 1997)  LR- 0.05
-     quote: "absence of murmur radiation to the right carotid artery (negative likelihood ratio, 0.05-0.10)"
```

Both are range endpoints from the same abstract. **This deletion alone leaves the
record with no estimate for a late-peaking murmur at all** — only two component
findings (diminished S2, radiation to the neck). See the Class B add in §3b.

### 5. `pocus_pericardial_effusion` — delete estimates [2] and [3]

```
- [2] src=2 (Mercé 1999)  sens 0.60 / spec 0.90  "right ventricular collapse"
- [3] src=2 (Mercé 1999)  sens 0.90 / spec 0.65  "collapse of any right cardiac chamber"
```

Mercé's reference standard is *clinical tamponade* and the index test is
echocardiographic chamber collapse, in patients already known to have an
effusion. This record's question is "is there an effusion?" — storing those rows
as ordinary accuracy answers a different question with a reversed design.

**After:** Mandavia (sens 0.96 / spec 0.98 / LR+ 48) + Netherton eFAST
(0.91 / 0.94) — exactly extractor-A's set. If we ever add a tamponade record the
Mercé rows belong there.

### 10. Empty estimates — delete 6 rows

Each of these has no sensitivity, specificity, likelihood ratio or prevalence
value. They render as an evidence row with nothing in it.

| Record | idx | What the quote actually contains |
|---|---|---|
| `exam_abdominal_distension` | 0 | RR 13.1 — a risk ratio, correctly *not* entered as an LR |
| `hx_prior_abdominal_surgery` | 0 | RR 12.1 — same |
| `exam_saddle_anesthesia_anal_tone` | 0 | "sensitivity … ranged from 0.19 … to 0.43" across several different red flags |
| `hx_dizziness_timing_triggers` | 0 | test–retest reliability (52% changed descriptor), explicitly labelled "not a diagnostic-accuracy estimate" |
| `hx_pleuritic_chest_pain` | 1 | "LRs 0.2-0.3" for a four-item composite |
| `pocus_lv_function_eyeball` | 0 | weighted agreement 84%, kappa 0.61 — an agreement statistic, not accuracy |

**Three records become estimate-less and must flip to `not_quantified`:**
`exam_abdominal_distension`, `hx_prior_abdominal_surgery`,
`exam_saddle_anesthesia_anal_tone`. Their sources stay (the manoeuvre is still
supported; only the numbers go), which is the case `tools/pull_decisions.py`
already handles. `pocus_lv_function_eyeball` stays `quantified` on its remaining
four rows; `hx_dizziness_timing_triggers` and `hx_pleuritic_chest_pain` stay
`partially_quantified`.

---

## Class B — fixes the verifier cannot express

### 3b. `exam_murmur_late_peaking_systolic` — add extractor-A's estimate

Add, at index 0, extractor-A's row for the record's *actual* finding, from
Shellenberger 2023 (already `sources[1]`):

```json
{
  "target_condition": "Aortic stenosis (late-peaking systolic ejection murmur)",
  "population": "Narrative aggregate of 4 small studies of patients with systolic murmurs (not bivariate meta-analysed)",
  "setting": "mixed",
  "reference_standard": "Echocardiography or left heart catheterization; AS of at least moderate severity",
  "sensitivity": null, "specificity": null,
  "lr_positive": {"value": 3.7, "ci_low": null, "ci_high": null},
  "lr_negative": {"value": 0.2, "ci_low": null, "ci_high": null},
  "computed": false,
  "interpretation_label": "both",
  "evidence_level": "pooled",
  "source_index": 1,
  "quote": "Data from a small sample from 4 studies revealed modest positive predictive value when this sign is present (LR of 3.7)",
  "location": "Discussion, paragraph on murmur characteristics (same paragraph: 'negative predictive value of its absence (LR = 0.2)')"
}
```

Both numbers are covered by the quote and location. Without this the record would
claim quantified evidence for a finding it does not quantify.

### 4. `exam_shock_index` — label the two outcome rows

```
  [0] target_condition: "Hemorrhage requiring hemostasis intervention after trauma — SI >0.9 …"
+ [0] target_condition: "PROGNOSTIC: Hemorrhage requiring hemostasis intervention after trauma — SI >0.9 …"
  [1] target_condition: "Hemorrhage requiring hemostasis intervention after trauma — SI >=0.8 …"
+ [1] target_condition: "PROGNOSTIC: Hemorrhage requiring hemostasis intervention after trauma — SI >=0.8 …"
```

Only [0] and [1]. Estimates [2]–[4] target concurrent states (hyperlactatemia
≥4.0 mmol/L; tubal rupture at surgery) and are correctly stored as diagnostic
accuracy. Extractor-A labelled its two outcome rows `PROGNOSTIC:` and the
promoted B packet did not.

*Rejected alternative:* flipping to extractor-A loses the sepsis and ectopic
strata (3 estimates) to gain 2.

### 6. `pocus_bladder_volume` — fabricated first author

This is the most serious defect in the set: a **name that is not in the paper**
sits in a verified record.

```
- sources[0].citation: "Beacock CJ, et al. (author list per PubMed) Accuracy of Bladder
-   Scanner for the Assessment of Postvoid Residual Volumes in Women With Pelvic Organ
-   Prolapse. Female Pelvic Med Reconstr Surg. 2021;27(1):e39-e42."
- sources[0].doi: null
+ sources[0].citation: "Taylor DL, Sierra T, Duenas-Garcia OF, Kim Y, Leung K, Hall C,
+   Flynn MK. Accuracy of Bladder Scanner for the Assessment of Postvoid Residual Volumes
+   in Women With Pelvic Organ Prolapse. Female Pelvic Med Reconstr Surg. 2021;27(1):e39-e42."
+ sources[0].doi: "10.1097/SPV.0000000000000645"
```

Verified against PubMed 30325783 just now. "Beacock" appears nowhere in the
paper; extractor-B's own notes admit the tool did not return an author list, so
the name was invented. The *numbers* are real and match the abstract.

**Second, separate decision — the estimates point the wrong way.** Both B rows
define the positive state as PVR **< 100 mL**, the inverse of this record's
question ("is the bladder full?"). Storing that as `sensitivity` of a
retention-threshold record inverts the meaning.

- **(i) Recommended — flip the base packet to extractor-A.** One estimate,
  Lukasse (PMID 17851812), 400 mL threshold, sens 0.76 / spec 0.96, quote
  "using the clinically desired value of a 400-ml threshold, are 0.76 and 0.96".
  Right direction, right threshold, no fabricated citation. Population is
  postpartum women.
- (ii) Keep B's rows and rewrite each `target_condition` to state the target
  explicitly as "PVR < 100 mL by catheter".

Under either option the card needs the population caveat: the evidence is from
postpartum and prolapse-clinic women, not the elderly-retention, post-operative
or cauda-equina patients this record is retrieved for.

### 7. `exam_abdominal_rigidity_guarding` — author list from the wrong paper

```
- sources[0].citation: "Kharbanda AB, Taylor GA, Fishman SJ, Bachur RG. Atypical clinical
-   features of pediatric appendicitis. Acad Emerg Med. 2007;14(2):124-129."
- sources[0].doi: null
+ sources[0].citation: "Becker T, Kharbanda A, Bachur R. Atypical clinical features of
+   pediatric appendicitis. Acad Emerg Med. 2007;14(2):124-129."
+ sources[0].doi: "10.1197/j.aem.2006.08.009"
```

Verified against PubMed 17192449 just now. The title, journal, year and pages are
right; the author list is Kharbanda's *2005 Pediatrics* decision-rule paper
(PMID 16140712). Both quoted numbers — "lack of guarding (LR, 0.63)" and "lack of
guarding (47%)" — are in the real abstract.

I checked the whole store: this fabricated author list and "Beacock" each appear
in exactly one record. No other verified record cites PMID 17192449.

**Second, separate decision — the numbers are pediatric.** Median age 11.9 y,
under an adult abdominal-pain record; extractor-A found nothing quotable for
adults and went `not_quantified`.

- **(i) Recommended — keep, and append "(pediatric)" to both `target_condition`
  strings** so the card cannot present them as adult data.
- (ii) Drop both estimates → `not_quantified`, matching extractor-A.

### 8. `fn_single_breath_count` — trace one row to its primary

Estimate [2] is currently sens 0.80 with **specificity null**, population "MG
patients (cohort as tabulated in systematic review; **attribution ambiguous**
between refs 17 and 21)", cited to the review's Table 3. Extractor-A traced the
same row to the primary paper, which also supplies the missing specificity.

Add a new source (index 5):

```json
{"citation": "Kukulka K, Gummi RR, Govindarajan R. A telephonic single breath count test for screening of exacerbations of myasthenia gravis: A pilot study. Muscle Nerve. 2020;62(2):258-261.",
 "doi": "10.1002/mus.26987", "pmid": "32447763", "url": null, "kind": "primary_study", "year": 2020}
```

Replace estimate [2] with extractor-A's row: 45 telephone calls from MG patients
with worsening symptoms, cutoff count 25 — **sens 0.80, spec 0.60, LR+ 2.0,
LR− 0.33**, quote "the nurse-administered telephonic SBCT had a positive
predictive value of 71%, sensitivity of 80%, and specificity of 60%",
`source_index: 5`.

The other two attribution disputes between the packets resolve **in favour of the
packet you promoted** — the ">19, sens 95%" row is Kalita 2020 and the "≤21,
94.4%/76.62%" row is Bartfield 1994, both as B recorded them. No change there.

### 9. `hx_palpitations_before_syncope` — estimate contradicts the prose

The single estimate is sens 0.08 / spec 0.89 / **LR+ 0.74** / LR− 1.03, computed
correctly from Berecki-Gisolf Table 2 (39/468 cardiac vs 200/1768 non-cardiac).
An LR+ below 1 means palpitations before syncope argued *against* cardiac syncope
in that pooled sample; the paper's model excluded the variable (p = 0.06).

`interpretation.positive_finding` currently reads:

> "Palpitations immediately before syncope, especially without autonomic prodrome
> and in a patient with structural heart disease, raise concern for arrhythmic
> syncope (EGSYS assigns it +4 points)."

A card would print a rule-in narrative directly above a below-1 likelihood ratio.

- **(i) Recommended — keep the number, rewrite the prose:**

  > "In the largest pooled literature sample (Berecki-Gisolf 2013, 468 cardiac vs
  > 1768 non-cardiac) palpitations before syncope did not discriminate: LR+ 0.74,
  > and the variable was excluded from the final model (p = 0.06). The EGSYS score
  > nonetheless assigns palpitations +4 points, so a score-based workflow and this
  > pooled estimate disagree. Treat palpitations as a prompt to characterise the
  > episode (abrupt onset/offset, absence of autonomic prodrome, structural heart
  > disease), not as independent evidence of arrhythmic syncope."

- (ii) Drop the estimate → `not_quantified`, matching extractor-B. This loses a
  real, correctly computed, `computed_from`-documented number.

I prefer (i): the discrepancy between a scoring convention and the pooled data is
itself the clinically useful content, and it is exactly the kind of thing the
tool exists to surface.

---

## What I need from you

1. **Class A (12 estimate deletions across 10 records)** — re-open these in the
   iPad verifier and exclude the listed rows, or tell me to apply them:
   `exam_carotid_upstroke_delayed`[1], `exam_chest_wall_tenderness_reproducible`[2],
   `exam_murmur_late_peaking_systolic`[0][1], `pocus_pericardial_effusion`[2][3],
   `exam_abdominal_distension`[0], `hx_prior_abdominal_surgery`[0],
   `exam_saddle_anesthesia_anal_tone`[0], `hx_dizziness_timing_triggers`[0],
   `hx_pleuritic_chest_pain`[1], `pocus_lv_function_eyeball`[0].
2. **Two citation corrections** (§6, §7) — these are factual errors against
   PubMed and I recommend applying them regardless of the other decisions.
3. **Four judgement calls:**
   - §6 bladder volume: flip to extractor-A *(recommended)* or relabel B's targets?
   - §7 rigidity: keep pediatric numbers with a "(pediatric)" label *(recommended)*
     or drop to `not_quantified`?
   - §9 palpitations: rewrite the prose *(recommended)* or drop the estimate?
   - §3b / §4 / §8: apply as written? *(recommended)*

Say which and I will run the command on the real store, commit, and report.

---

## How to apply, and what I already checked

`tools/apply_fixes.py` implements every change above. It is a **dry run by
default** and has not been run against `records/verified/`:

```bash
python3 tools/apply_fixes.py                 # print the diff, write nothing
python3 tools/apply_fixes.py --apply         # the recommended options
python3 tools/apply_fixes.py --apply --bladder relabel --rigidity drop --palpitations drop
```

Each deletion is matched on a fragment of the estimate's **own quote**, not on a
position, so the script is idempotent and stays correct if rows move. A fragment
that matches two rows refuses to delete either. Every change is appended to the
record's `verification_notes` as an `[owner fix]` line with its reason, and bumps
`record_version` — the store stays self-documenting about what was changed after
promotion.

I ran both option sets end to end against a **throwaway copy** of the repo, not
the real store:

| | now | recommended options | alternative options |
|---|---|---|---|
| records | 153 | 153 | 153 |
| estimates | 349 | 337 | 335 |
| quantified / partial / not_quantified | 83 / 36 / 34 | 83 / 33 / 37 | 82 / 32 / 39 |
| `not_quantified` share | 22.2% | 24.2% | 25.5% |
| validator | 0 errors, 14 warnings | 0 errors, 8 warnings | 0 errors, 8 warnings |
| re-running the script | — | 0 further changes | 0 further changes |

The test suite passes on the fixed store (131 passed; the freeze tests are
excluded there only because a copy outside a git working tree cannot run
`git show`, and they pass on the real repo — 204 passed).

### One tooling bug found on the way

`tools/validate.py` was not detecting empty estimates. Its check was
`any(est.get(k) for k in (...))`, and a stat field is stored as
`{"value": null, "ci_low": null, "ci_high": null}` — a non-empty dict, which is
truthy. So a row whose numbers were all null passed the check whenever the key
was present. It also ignored `prevalence`, which is a legitimate thing for a row
to report on its own.

Fixed: test `.value`, and count `prevalence`. On the current store the corrected
check reports exactly the 6 empty rows listed above, and stops mis-flagging the
two prevalence-only rows in `hx_pleuritic_chest_pain` and `hx_vte_risk_factors`.
That is a change to the tooling only — it touches no record.
