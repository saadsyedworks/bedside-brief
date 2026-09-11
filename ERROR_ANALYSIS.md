# Error analysis — arm A, shipped configuration

Run: `eval/runs/20260911T113543Z-vitals-no-avoidwhen` (108 frozen inputs, `observed_values` on,
`RANKER_CONTRAINDICATIONS="off"`). Numbers from `metrics.json` and recomputed from the stored
per-case outputs; the classification below is not in the harness and was derived by walking each
missed target back through that case's own candidate list.

Headline: recall 71.0% of must-have targets (74.4% where the library covers the target), 0.0%
unsupported quantitative claims, 100% evidence fidelity, 6.06 items per card, 3 violations of 108.

## The 88 missed must-have target instances, by mechanism

| | mechanism | share | what fixes it |
|---|---|---|---|
| 1 | **Ranking / card capacity** — the record was offered to the ranker and did not make the 8 slots | **44 (50%)** | better ranking, or more slots |
| 2 | **Retrieval** — the record exists and was never offered as a candidate | **22 (25%)** | indexing (`clinical_mapping`), not new records |
| 3 | **Coverage** — no library record for the target at all | **22 (25%)** | expanding the library |

**This revises the answer I gave on library expansion.** I said the recall gap against arm C was
library coverage. That is true of the *stratum comparison* — arm A scores 18.5% on the 27 must-have
targets with no record while arm C scores 63.0% — but it is not true of the absolute misses. Only a
quarter of them are coverage. Half are a card with eight slots and a ranker filling them, and the
dilution measurement points the same way: inputs offered ~16 candidates recall 71.9% of must-have
targets, inputs offered ~30 recall 66.7%. **Expanding the library addresses at most a quarter of
this gap and makes the dominant half worse.** The cheap win is mechanism 2.

## 1. Ranking / card capacity — 44 instances (50%)

The eight slots are the binding constraint. Retrieval offers a mean of 23 candidates and the ranker
discards about 17 of every 23, so half of all misses are items the system found, judged, and dropped.

| missed | record | chosen on other cases |
|---|---|---|
| 8× | `exam_s3_gallop` | 1× |
| 4× | `exam_orthostatic_vitals` | 18× |
| 4× | `exam_capillary_refill` | 1× |
| 3× | `exam_abdominojugular_reflux` | 5× |
| 3× | `exam_chest_wall_tenderness_reproducible` | 2× |
| 3× | `exam_tachypnea_rr_gt24` | 7× |
| 2× | `fn_forced_expiratory_time` | **0×** |

Two distinct problems hide in that column. `exam_orthostatic_vitals` and `exam_jvp_elevated` are
chosen 18 and 27 times elsewhere — the ranker likes them, it just had something better on those
cases, which is defensible behaviour. `exam_s3_gallop` (8 misses, 1 selection) and
`fn_forced_expiratory_time` (2 misses, never selected) are different: the ranker systematically
under-values them. S3 gallop is the single most-missed target in the whole run and is a must-have
across chest pain, dyspnea and edema.

Concentrated in hypotension (9), AKI (7), chest pain (7) and syncope (6) — the presentations with
the most candidates, which is what the dilution result predicts.

## 2. Retrieval never offered the record — 22 instances (25%)

These are indexing gaps. The record is verified, relevant, and sitting in the store unreachable for
that presentation because its `clinical_mapping` does not connect it.

| missed | record | case it was needed for |
|---|---|---|
| 3× | `hx_deliriogenic_medication_review` | `aki_002`, `ams_001` — deliriogenic drug review in AKI/AMS |
| 3× | `exam_cva_tenderness` | `ams_001` — urinary source for delirium |
| 3× | `exam_rebound_tenderness` | `ams_*` — abdominal source |
| 3× | `exam_melena_rectal_exam` | `ams_*` |
| 3× | `exam_capillary_refill` | |
| 3× | `exam_conjunctival_pallor` | |

The pattern is cross-presentation: exam records indexed under abdominal pain or hypotension that a
delirium work-up needs. Retrieval has a cross-presentation fallback (2–4 candidates per case in the
logs), and it is not reaching these. **This is the highest-yield fix available and needs no new
extraction** — but `clinical_mapping` lives in verified records, so widening it is an owner
promotion, not something I change.

## 3. No library record — 22 instances (25%)

Structurally unreachable; arm A cannot recall what it has no record for. The recurring nine
must-have targets with no record (`benchmark/target_map.json#_unmapped`) are dominated by
*context-gathering* rather than manoeuvres:

- "Ask nurse and family: baseline cognition and function, what changed and when" (×3)
- "Establish last-known-well time precisely" (×3)
- "Ask about known COPD diagnosis or prior spirometry, home inhalers, prior exacerbations" (×3)
- "Inspect surgical wound for erythema, warmth, drainage, dehiscence" (×3)
- "Cannon a waves in the jugular venous pulse and variable intensity of S1" (×3)
- "Ask about onset (abrupt at rest vs after cough or strain), prior pneumothorax" (×2)

Four of the six are collateral history and chart review — the parts of an inpatient work-up that
have no diagnostic-accuracy literature to extract, so a store built from the Rational Clinical
Examination series and primary accuracy studies will never contain them. That is a finding about the
approach, not a to-do: **an evidence-grounded store can only recommend what has been measured**, and
a meaningful part of good bedside practice has not been.

## 4. Ask-first false negatives — 3 cases

`weakness_003` and its variants. "Too weak to walk today" — a genuine judgement call, already
disclosed as the residual disagreement in DECISIONS #30. No false positives in 108 inputs.

## 5. should_not_recommend violations — 3 cases

All three `hypotension_002` variants recommend orthostatic vitals for a patient at supine 88/54.
Eliminated by `RANKER_CONTRAINDICATIONS="all"` at a cost of ten points of perturbation
responsiveness, and the owner's decision (DECISIONS #48) is to ship without it. This must appear in
the abstract's limitations, not only in a table.

## What I would fix, in order

1. **Retrieval indexing** (mechanism 2, 25% of misses, no new extraction). Needs owner promotion of
   widened `clinical_mapping` on about six records.
2. **Ranker under-valuation of specific records** (`exam_s3_gallop`, `fn_forced_expiratory_time`).
   Worth checking whether their `changes_what` text reads as weaker than the evidence warrants —
   that string is most of what the ranker sees.
3. **Card capacity.** Eight slots is a product decision and brevity is a selling point, so this is a
   trade to state rather than silently resolve.
4. **Library expansion** last, not first: a quarter of the benefit and it worsens the dominant half.
