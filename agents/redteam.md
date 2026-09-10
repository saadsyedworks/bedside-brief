# Red-team subagent

Review a batch of extraction packets. Flag; do not fix. Output `records/redteam/{batch}.md` listing per record id:

- **NUMERIC MISMATCH**: packets A and B report different values for the same estimate.
- **NO LOCATION**: a numeric estimate lacks a verbatim quote or table/page/figure.
- **SECONDARY SOURCE**: the cited source is a textbook, narrative review, UpToDate, McGee, or similar.
- **SILENT COMPUTATION**: sens/spec/LR appear derived but `computed` is false or `computed_from` is empty.
- **POPULATION COLLAPSE**: a single estimate where the source reports materially different performance by population/setting.
- **VOCAB VIOLATION**: any presentation/differential/tag not in `vocab.json`.
- **SCOPE**: POCUS record missing `skill_assumption`; contraindications missing where obviously relevant.
- **FABRICATION SUSPECT**: a citation that cannot be resolved (DOI/PMID lookup fails) or a quote that does not appear in the source.

End with a suggested verification order for the owner: FABRICATION SUSPECT and NUMERIC MISMATCH first, then rce_backed agreements, then the rest.
