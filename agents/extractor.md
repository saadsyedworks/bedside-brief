# Extractor subagent

You are extracting one bedside discriminator record for Bedside Brief. Follow `extraction_packet_spec.md` exactly and output one JSON object valid against `discriminator_schema.json` with `tier: "extracted"`.

Input: a discriminator id, title, type, presentations[], differentials[] from `discriminator_ids.json`, plus `vocab.json`.

Procedure:
1. Search for diagnostic-accuracy evidence. Start with the JAMA Rational Clinical Examination series for this finding; then systematic reviews/meta-analyses of diagnostic accuracy; then prospective primary studies. Use McGee's Evidence-Based Physical Diagnosis only as an index to locate primary studies — never cite it as the source of a number.
2. For every estimate, capture: target condition, population, setting, reference standard, prevalence if reported, sens/spec/LR± with CIs, the verbatim ≤25-word quote containing the number, and its table/page/figure. No location → estimate is null and say why in `extraction_notes`.
3. If estimates differ materially by population or technique, add separate `estimates[]` entries. Do not average.
4. If nothing quantitative is defensible, set `evidence_status: "not_quantified"`, `estimates: []`, and cite the guideline/consensus supporting the maneuver.
5. Write technique / positive_finding / negative_finding / pitfalls / changes_what in plain clinical language, ≤2 sentences each, `changes_what` ≤200 chars.
6. Use only `presentations`, `differentials`, `indication_tags` strings from `vocab.json`.
7. Do not fill `tier` (leave "extracted"), `verified_by`, `verified_at`, `verification_notes`.

You are one of two independent extractors. Do not look for or reuse another packet. Save to `records/extracted/{id}__{agent_id}.json`.
