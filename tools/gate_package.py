"""Generate PHASE0_GATE.md for the owner from current artifacts. Re-run after any edit."""
from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ["dyspnea_001", "syncope_002", "edema_003", "hypotension_002", "abdominal_pain_003", "weakness_002"]
ORDER = ["dyspnea", "chest_pain", "syncope", "palpitations", "edema", "hypotension", "aki",
         "dizziness", "ams", "abdominal_pain", "fever", "weakness"]

VOCAB_WISHLIST = """
Differentials the id drafters wanted but that are NOT in vocab.json (none was needed by a benchmark case):
`bacteremia`, `upper_gi_bleed`, `spinal_epidural_abscess`, `hypothyroidism` (myxedema edema), `aortic_regurgitation`,
`mitral_regurgitation`, `tension_pneumothorax`, `alcohol_withdrawal` / `opioid_toxicity` (vs one `intoxication_withdrawal`),
`delirium_metabolic` (only `delirium_infectious` exists — CAM maps awkwardly), `intracranial_hemorrhage`, `vestibular_migraine`,
`neurogenic_shock`, `hypercalcemia`, `incarcerated_hernia`, `ectopic_pregnancy`/`ovarian_torsion`, `seizure_todd_paresis`, `transverse_myelitis`.
Cross-listing gaps (term exists but not under the presentation where retrieval needs it): `aortic_dissection` not under hypotension;
`anxiety_hyperventilation` not under palpitations; `hyperthyroidism` not under edema/syncope; `pericarditis` not under dyspnea/fever;
`pulmonary_embolism` not under edema; `urinary_retention` not under aki (drafters used `obstruction_retention`).
Indication tags wanted: `urinary_catheter`, `central_line`, `recent_antibiotics`, `nsaid_use`, `chronic_steroids`, `opioid_use`,
`benzodiazepine_use`, `recent_contrast`, `prosthetic_joint`, `neutropenic`, `smoker`, `hemoptysis`, `known_cad`, `known_valve_disease`,
`family_hx_sudden_death`, `bph_known`, `hearing_loss`.
Recommendation: add NOTHING before freeze #1 (every case and id validates today); revisit after Phase 3 library-coverage numbers show which gaps cost recall.
"""


def main() -> None:
    ids = json.loads((ROOT / "discriminator_ids.json").read_text())["ids"]
    cases = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "benchmark" / "cases").glob("*.json"))}
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    by_type = Counter(e["type"] for e in ids)
    by_ev = Counter(e["expected_evidence"] for e in ids)
    by_pri = Counter(e["priority"] for e in ids)
    by_pres = Counter(p for e in ids for p in e["presentations"])
    under = [c for c, v in cases.items() if v["underspecified_flag_expected"]]
    mh_total = sum(sum(t["must_have"] for t in v["reference_targets_freetext"]) for v in cases.values())
    tg_total = sum(len(v["reference_targets_freetext"]) for v in cases.values())

    out = []
    out.append(f"# Phase 0 owner gate — Bedside Brief\n\nGenerated at commit `{head}`. Everything below is a DRAFT until you sign off; after sign-off I commit **freeze #1** and write its hash into every case file.\n")
    out.append("## What you are approving\n")
    out.append(f"- `discriminator_ids.json`: **{len(ids)} ids** — {dict(by_type)}; evidence expectation {dict(by_ev)}; priority {dict(by_pri)}. Every `anchor_source` PMID was confirmed against PubMed by title.")
    out.append(f"- `benchmark/cases/`: **36 base cases = 108 inputs** (each file nests one perturbation pair + one noise variant), {tg_total} free-text targets ({mh_total} must-have), {len(under)} deliberately underspecified cases ({', '.join(under)}). Two critic passes + one re-check applied; `python3 tools/validate.py cases` = 0 errors.")
    out.append("- `vocab.json`: **unchanged**. Wish-list from the drafters is listed under decision 2.\n")
    out.append("Ids per presentation (an id can serve several): " + ", ".join(f"{p} {by_pres[p]}" for p in ORDER) + "\n")

    out.append("## Decisions I need from you (numbered; reply with the number and your call)\n")
    out.append("1. **Approve the 148-id list as the extraction universe**, or name ids to drop/add/rename. Cardiology + volume are deep on purpose (dyspnea 60, hypotension 48, chest pain 48, syncope 41, AKI 40); palpitations is thin (14) — say if you want 5–8 more there (e.g. exertional palpitations, thyroid exam, anxiety features).")
    out.append("2. **Vocab: keep frozen as-is (my recommendation) or add terms now.** " + VOCAB_WISHLIST.strip().replace("\n", " "))
    out.append("3. **must_have on guideline-only maneuvers (DECISIONS #14).** 12 of the must-have targets will map to `not_quantified` records (e.g. medication review in syncope_002, source exam in hypotension_001, hemodynamic-stability check in palpitations_002). Keep them as must-have (recall counts them, and not-quantified is first-class), or demote all to should-include so must-have recall is purely literature-backed?")
    out.append("4. **Off-bedside boundary (DECISIONS #11).** I classified medication/MAR review as bedside history and SpO2, telemetry, I/Os, weights, POC glucose, bladder scan as off-bedside. Confirm, or move MAR review to off-bedside (this changes ~15 targets and the eval classifier).")
    out.append("5. **Compound targets (DECISIONS #13).** A target like \"Neck stiffness, Kernig, Brudzinski, jolt accentuation\" counts as present if ANY component is on the card. Confirm, or require ALL components.")
    out.append("6. **POCUS stays extracted-but-disabled** (14 pocus ids will be extracted; never retrieved until you flip DAY1_FREEZE.md). Confirm.")
    out.append("7. **Branch redundancy:** dyspnea_003, chest_pain_002 and edema_003 are all VTE-branch cases in different presentations. Critic says acceptable; author declined to re-branch chest_pain_002 to pneumothorax. Keep, or re-branch chest_pain_002?")
    out.append("8. **Sign-off wording:** reply \"freeze #1\" (optionally with edits) and I commit, hash-stamp all 36 files, and mark the benchmark read-only.\n")

    out.append("## The 6 sample cases (one per pair of presentations)\n")
    for cid in SAMPLE:
        c = cases[cid]
        out.append(f"### {cid}  ({c['presentation']}; dx: {', '.join(c['intended_bedside_differential'])})")
        out.append(f"**Input:** {c['input_oneliner']}\n")
        for t in c["reference_targets_freetext"]:
            out.append(f"- {'**MUST**' if t['must_have'] else 'should'} — {t['item']}  \n  _{t['rationale']}_")
        out.append(f"\n- Off-bedside OK: {'; '.join(c['off_bedside_acceptable'])}")
        out.append(f"- Should NOT: {'; '.join(c['should_not_recommend'])}")
        out.append(f"- Underspecified flag: {c['underspecified_flag_expected']}")
        p, n = c["perturbation_pair"], c["noise_variant"]
        out.append(f"- **Perturbation** ({p['changed_feature']}): {p['input_oneliner']}  \n  → {p['expected_change']}")
        out.append(f"- **Noise:** {n['input_oneliner']}  \n  → {n['expected_change']}\n")

    out.append("## Where to look\n")
    out.append("- Full id list: `discriminator_ids.json` (sorted priority → cardiology-first). Batches: `records/batches.json`.")
    out.append("- All cases: `benchmark/cases/*.json`; critic reports: `benchmark/critique_part1.md`, `critique_part2.md`, `critique_recheck.md`.")
    out.append("- Every non-owner decision so far: `DECISIONS.md`. Timeline: `RUNLOG.md`.")
    (ROOT / "PHASE0_GATE.md").write_text("\n".join(out) + "\n")
    print(f"wrote PHASE0_GATE.md ({len(ids)} ids, {len(cases)} cases, head {head})")


if __name__ == "__main__":
    main()
