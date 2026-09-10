# Extraction Packet Spec (for AI research agents)

Each discriminator gets TWO packets from independent agent runs. The owner diffs them.

## Output: one JSON object matching discriminator_schema.json with tier = "extracted"

## Hard rules
1. Every numeric estimate MUST include: primary citation (DOI or PMID), a verbatim quote of ≤25 words containing the number, and its exact location (table number / page / figure). No location → set the estimate to null and explain in `extraction_notes`.
2. Cite only primary diagnostic-accuracy studies or pooled analyses (RCE series, systematic reviews). If you found the number in McGee, UpToDate, a narrative review, or a textbook, trace it to the primary source and cite THAT. If you cannot, the estimate is null.
3. Record population, setting, reference standard, and disease definition for every estimate. If an estimate differs materially by population, add a second `estimates[]` entry — do not average.
4. If no defensible quantitative data exist, set `evidence_status = "not_quantified"` and cite the guideline or consensus source for the maneuver's use.
5. Never infer a sensitivity/specificity from an LR or vice versa unless the source reports the 2×2; if you compute, set `computed = true` and show the input numbers.
6. POCUS estimates must record operator level, protocol, threshold, and comparator.
7. Write `technique`, `positive_finding`, `negative_finding`, `pitfalls` in plain clinical language, ≤2 sentences each. No hedging filler.

## Fields you fill
identity, clinical_mapping, technique, interpretation, estimates[], evidence_status, sources[], safety_scope, extraction_notes, agent_id, extracted_at.

## Fields you never touch
tier, verified_by, verified_at, verification_notes, record_version.

## Deliver as
`/records/extracted/{id}__{agent_id}.json`
