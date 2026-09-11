"""Apply the approved red-team fixes to records/verified/ (see PROPOSED_FIXES.md).

  python3 tools/apply_fixes.py                      # dry run: print the diff, write nothing
  python3 tools/apply_fixes.py --apply              # write, using the recommended options
  python3 tools/apply_fixes.py --apply --bladder relabel --palpitations drop

Nothing here invents evidence. Every deletion removes a row the red team traced to a
between-study range, a reversed reference standard, or no number at all; every citation
change was re-fetched from PubMed; the two additions are estimator-A rows that already
carry their own quote and location. Each edit is appended to the record's
verification_notes as an `[owner fix]` line and bumps record_version, so the verified
store stays self-documenting about what was changed after promotion.

Idempotent: a fix whose effect is already present is reported as "already applied" and
the record is left untouched.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate import validate_records  # noqa: E402

VERIFIED = ROOT / "records" / "verified"
NUMERIC = ("sensitivity", "specificity", "lr_positive", "lr_negative", "prevalence", "ppv", "npv")


# --- the fixes -------------------------------------------------------------------------

# Estimates to delete, keyed by record id. Each is matched on a fragment of its own quote rather
# than on a position, so the fix stays idempotent and stays correct even after another row has been
# added or removed above it. A fragment that matches nothing means the row is already gone; a
# fragment that matches more than one row is an error, not a guess.
DELETIONS: dict[str, list[tuple[str, str]]] = {
    "exam_carotid_upstroke_delayed": [
        ("positive likelihood ratio, 2.8-130",
         "LR+ 2.8 is the low end of the between-study range 2.8-130 in the Etchells 1997 "
         "abstract, not a point estimate; the pooled value for this finding is LR+ 9.04"),
    ],
    "exam_chest_wall_tenderness_reproducible": [
        ("LR range, 0.2-0.4",
         "LR+ 0.2 is the low end of the range 0.2-0.4 quoted from the 1998 Rational Clinical "
         "Examination; the record already carries two real point estimates (0.23 and 0.3)"),
    ],
    "exam_murmur_late_peaking_systolic": [
        ("positive likelihood ratio, 8.0-101",
         "LR+ 8.0 is the low end of the between-study range 8.0-101 in the Etchells 1997 abstract"),
        ("negative likelihood ratio, 0.05-0.10",
         "LR- 0.05 is the low end of the range 0.05-0.10 in the same sentence of the same abstract"),
    ],
    "pocus_pericardial_effusion": [
        ("60% and 90% for right ventricular collapse",
         "Merce 1999 uses clinical tamponade as the reference standard and chamber collapse as "
         "the index test, in patients already known to have an effusion; stored here it answered "
         "a different question with a reversed design"),
        ("90% and 65% for the presence of any collapse",
         "same reversed design as the preceding row"),
    ],
    # Estimates carrying no sensitivity, specificity, likelihood ratio or prevalence at all.
    "exam_abdominal_distension": [
        ("abdominal distension (yes versus no) (RR = 13.1)",
         "no accuracy number: the quote reports a risk ratio (RR 13.1), correctly not entered as an LR"),
    ],
    "hx_prior_abdominal_surgery": [
        ("previous abdominal surgery (relative risk (RR) = 12.1)",
         "no accuracy number: the quote reports a risk ratio (RR 12.1)"),
    ],
    "exam_saddle_anesthesia_anal_tone": [
        ("pooled sensitivity for the signs and symptoms ranged from 0.19",
         "no accuracy number: the quote gives a sensitivity range spanning several different red flags"),
    ],
    "hx_dizziness_timing_triggers": [
        ("picked a different response on retest",
         "not a diagnostic-accuracy estimate (test-retest reliability of the descriptor), as the "
         "row's own target_condition says"),
    ],
    "hx_pleuritic_chest_pain": [
        ("stabbing, pleuritic, positional, or reproducible by palpation",
         "no accuracy number: 'LRs 0.2-0.3' is a range over a four-item composite"),
    ],
    "pocus_lv_function_eyeball": [
        ("weighted agreement between EPs and the primary cardiologist was 84%",
         "no accuracy number: weighted agreement 84% and kappa 0.61 are agreement statistics"),
    ],
}

# Citation corrections, re-fetched from PubMed. (record id, pmid) -> replacement fields.
CITATIONS: dict[tuple[str, str], dict] = {
    ("pocus_bladder_volume", "30325783"): {
        "citation": "Taylor DL, Sierra T, Duenas-Garcia OF, Kim Y, Leung K, Hall C, Flynn MK. "
                    "Accuracy of Bladder Scanner for the Assessment of Postvoid Residual Volumes "
                    "in Women With Pelvic Organ Prolapse. Female Pelvic Med Reconstr Surg. "
                    "2021;27(1):e39-e42.",
        "doi": "10.1097/SPV.0000000000000645",
        "_why": "the promoted packet credited a first author ('Beacock CJ') who does not appear in "
                "the paper; PubMed 30325783 is Taylor DL et al.",
    },
    ("exam_abdominal_rigidity_guarding", "17192449"): {
        "citation": "Becker T, Kharbanda A, Bachur R. Atypical clinical features of pediatric "
                    "appendicitis. Acad Emerg Med. 2007;14(2):124-129.",
        "doi": "10.1197/j.aem.2006.08.009",
        "_why": "the promoted packet carried the author list of Kharbanda's 2005 Pediatrics "
                "decision-rule paper (PMID 16140712); PubMed 17192449 is Becker T, Kharbanda A, "
                "Bachur R. The quoted numbers are correct.",
    },
}

# target_condition prefixes/suffixes. (record id) -> list of (index, mode, text, why)
LABELS: dict[str, list[tuple[int, str, str, str]]] = {
    "exam_shock_index": [
        (0, "prefix", "PROGNOSTIC: ",
         "the target is an outcome (bleeding requiring an intervention for hemostasis), not a "
         "concurrent state; extractor-A labelled its equivalent rows and the promoted packet did not"),
        (1, "prefix", "PROGNOSTIC: ", "same outcome at a lower shock-index threshold"),
    ],
}

MURMUR_ADD = {
    "target_condition": "Aortic stenosis (late-peaking systolic ejection murmur)",
    "population": "Narrative aggregate of 4 small studies of patients with systolic murmurs "
                  "(not bivariate meta-analysed)",
    "setting": "mixed",
    "prevalence": None,
    "reference_standard": "Echocardiography or left heart catheterization; AS of at least moderate severity",
    "sensitivity": None,
    "specificity": None,
    "lr_positive": {"value": 3.7, "ci_low": None, "ci_high": None},
    "lr_negative": {"value": 0.2, "ci_low": None, "ci_high": None},
    "computed": False,
    "interpretation_label": "both",
    "evidence_level": "pooled",
    "quote": "Data from a small sample from 4 studies revealed modest positive predictive value "
             "when this sign is present (LR of 3.7)",
    "location": "Discussion, paragraph on murmur characteristics (same paragraph: 'negative "
                "predictive value of its absence (LR = 0.2)')",
}

SBC_SOURCE = {
    "citation": "Kukulka K, Gummi RR, Govindarajan R. A telephonic single breath count test for "
                "screening of exacerbations of myasthenia gravis: A pilot study. Muscle Nerve. "
                "2020;62(2):258-261.",
    "doi": "10.1002/mus.26987",
    "pmid": "32447763",
    "url": None,
    "kind": "primary_study",
    "year": 2020,
}

SBC_ESTIMATE = {
    "target_condition": "Myasthenia gravis exacerbation (telephonic screening, cutoff count 25)",
    "population": "45 telephone calls from MG patients reporting worsening symptoms "
                  "(single-center retrospective pilot)",
    "setting": "outpatient",
    "prevalence": None,
    "reference_standard": "Clinically diagnosed MG exacerbation after emergency department evaluation",
    "sensitivity": {"value": 0.8, "ci_low": None, "ci_high": None},
    "specificity": {"value": 0.6, "ci_low": None, "ci_high": None},
    "lr_positive": {"value": 2.0, "ci_low": None, "ci_high": None},
    "lr_negative": {"value": 0.33, "ci_low": None, "ci_high": None},
    "computed": True,
    "computed_from": "LR+ = 0.80 / (1 - 0.60) = 2.0; LR- = (1 - 0.80) / 0.60 = 0.33",
    "interpretation_label": "both",
    "evidence_level": "single_study",
    "quote": "the nurse-administered telephonic SBCT had a positive predictive value of 71%, "
             "sensitivity of 80%, and specificity of 60%",
    "location": "Abstract, Results",
}

PALPITATIONS_POSITIVE = (
    "In the largest pooled literature sample (Berecki-Gisolf 2013; 468 cardiac vs 1768 non-cardiac "
    "syncope episodes) palpitations before syncope did not discriminate: LR+ 0.74, and the variable "
    "was excluded from the final model (p = 0.06). The EGSYS score nonetheless assigns palpitations "
    "+4 points, so a score-based workflow and this pooled estimate disagree. Treat palpitations as a "
    "prompt to characterise the episode (abrupt onset and offset, absence of autonomic prodrome, "
    "structural heart disease) rather than as independent evidence of arrhythmic syncope."
)


# --- machinery -------------------------------------------------------------------------

def load(rid: str) -> dict:
    return json.loads((VERIFIED / f"{rid}.json").read_text())


def has_number(est: dict) -> bool:
    for k in NUMERIC:
        v = est.get(k)
        if (v.get("value") if isinstance(v, dict) else v) is not None:
            return True
    return False


class Changes:
    def __init__(self) -> None:
        self.per_record: dict[str, list[str]] = {}
        self.skipped: list[str] = []

    def add(self, rid: str, line: str) -> None:
        self.per_record.setdefault(rid, []).append(line)


def apply_all(opts: argparse.Namespace) -> tuple[dict[str, dict], Changes]:
    out: dict[str, dict] = {}
    ch = Changes()

    def rec_for(rid: str) -> dict:
        if rid not in out:
            out[rid] = load(rid)
        return out[rid]

    # 1. deletions ------------------------------------------------------------------
    for rid, rows in DELETIONS.items():
        rec = rec_for(rid)
        for fragment, why in rows:
            hits = [i for i, e in enumerate(rec["estimates"]) if fragment in str(e.get("quote", ""))]
            if not hits:
                ch.skipped.append(f"{rid}: already removed ({fragment[:40]}...)")
                continue
            if len(hits) > 1:
                ch.skipped.append(f"{rid}: AMBIGUOUS - {len(hits)} rows quote {fragment[:40]!r}; "
                                  f"not removing any")
                continue
            gone = rec["estimates"].pop(hits[0])
            ch.add(rid, f"removed estimate [{hits[0]}] "
                        f"\"{str(gone.get('target_condition'))[:70]}\" - {why}")
        if not rec["estimates"] and rec.get("evidence_status") != "not_quantified":
            rec["evidence_status"] = "not_quantified"
            ch.add(rid, "evidence_status -> not_quantified (no estimate remains; sources kept, "
                        "the manoeuvre is still supported)")

    # 2. citation corrections -------------------------------------------------------
    for (rid, pmid), fix in CITATIONS.items():
        if rid == "pocus_bladder_volume" and opts.bladder == "flip-a":
            # extractor-A never cites this PMID, so re-promoting from A removes the bad citation
            # outright; patching it first would only produce a note about an edit that is discarded.
            ch.skipped.append("pocus_bladder_volume: citation superseded by the flip to extractor-A")
            continue
        rec = rec_for(rid)
        for s in rec["sources"]:
            if s.get("pmid") != pmid:
                continue
            if s.get("citation") == fix["citation"]:
                ch.skipped.append(f"{rid} PMID {pmid}: citation already corrected")
                break
            old = s["citation"]
            s["citation"] = fix["citation"]
            s["doi"] = fix["doi"]
            ch.add(rid, f"corrected the citation for PMID {pmid} - {fix['_why']}\n"
                        f"      was: {old[:100]}\n"
                        f"      now: {fix['citation'][:100]}")
            break
        else:
            ch.skipped.append(f"{rid}: no source with PMID {pmid}")

    # 3. target_condition labels ----------------------------------------------------
    for rid, rows in LABELS.items():
        rec = rec_for(rid)
        for idx, mode, text, why in rows:
            est = rec["estimates"][idx]
            cur = est.get("target_condition", "")
            if cur.startswith(text) if mode == "prefix" else cur.endswith(text):
                ch.skipped.append(f"{rid}[{idx}]: label already present")
                continue
            est["target_condition"] = (text + cur) if mode == "prefix" else (cur + text)
            ch.add(rid, f"labelled estimate [{idx}] \"{text.strip()}\" - {why}")

    # 4. murmur: add extractor-A's row for the record's own finding ------------------
    rec = rec_for("exam_murmur_late_peaking_systolic")
    shellenberger = next((i for i, s in enumerate(rec["sources"]) if s.get("pmid") == "37377515"), None)
    if shellenberger is None:
        ch.skipped.append("exam_murmur_late_peaking_systolic: Shellenberger 2023 not in sources; row not added")
    elif any(e.get("quote", "").startswith("Data from a small sample from 4 studies") for e in rec["estimates"]):
        ch.skipped.append("exam_murmur_late_peaking_systolic: extractor-A row already present")
    else:
        row = dict(MURMUR_ADD, source_index=shellenberger)
        rec["estimates"].insert(0, row)
        ch.add("exam_murmur_late_peaking_systolic",
               "added extractor-A's estimate for a late-peaking murmur itself (Shellenberger 2023, "
               "LR+ 3.7 / LR- 0.2) - without it the record carried only component findings "
               "(diminished S2, radiation to the neck) and no estimate of its own sign")
        if rec.get("evidence_status") == "not_quantified":
            rec["evidence_status"] = "partially_quantified"

    # 5. single breath count: replace the review-table row with the traced primary ---
    rec = rec_for("fn_single_breath_count")
    if any(s.get("pmid") == "32447763" for s in rec["sources"]):
        ch.skipped.append("fn_single_breath_count: Kukulka 2020 already cited")
    else:
        rec["sources"].append(dict(SBC_SOURCE))
        idx = len(rec["sources"]) - 1
        target = next((i for i, e in enumerate(rec["estimates"])
                       if "attribution ambiguous" in str(e.get("population", ""))), None)
        if target is None:
            ch.skipped.append("fn_single_breath_count: the ambiguous-attribution row is gone; source added only")
        else:
            old = rec["estimates"][target]
            rec["estimates"][target] = dict(SBC_ESTIMATE, source_index=idx)
            ch.add("fn_single_breath_count",
                   f"replaced estimate [{target}] (sens 0.80, specificity absent, cited to the "
                   f"systematic review's Table 3 with \"attribution ambiguous between refs 17 and 21\") "
                   f"with the traced primary study, Kukulka 2020 (PMID 32447763): sens 0.80, spec 0.60, "
                   f"LR+ 2.0, LR- 0.33. Rule 2 requires tracing to the primary where it exists.")
            del old

    # 6. bladder volume -------------------------------------------------------------
    rec = rec_for("pocus_bladder_volume")
    if opts.bladder == "flip-a":
        a = json.loads((ROOT / "records" / "extracted" /
                        "pocus_bladder_volume__extractor-A.json").read_text())
        if rec.get("_base_packet") == "A":
            ch.skipped.append("pocus_bladder_volume: already on extractor-A")
        else:
            keep = {k: rec[k] for k in ("tier", "verified_by", "verified_at", "record_version") if k in rec}
            notes = rec.get("verification_notes", "")
            rec.clear()
            rec.update(a)
            rec.update(keep)
            rec["verification_notes"] = notes
            rec["_base_packet"] = "A"
            rec.pop("_anchor_source", None)
            rec.pop("_expected_evidence", None)
            ch.add("pocus_bladder_volume",
                   "re-promoted from extractor-A instead of extractor-B. A's single estimate "
                   "(Lukasse, PMID 17851812) is at a 400 mL retention threshold in the record's own "
                   "direction - sens 0.76 / spec 0.96 - whereas B's two rows define the positive "
                   "state as a post-void residual BELOW 100 mL, the inverse of this record's "
                   "question, and carried the invented 'Beacock' citation")
    else:
        for i, e in enumerate(rec.get("estimates", [])):
            tc = e.get("target_condition", "")
            if "PVR <100 mL" in tc:
                ch.skipped.append(f"pocus_bladder_volume[{i}]: target already restated")
                continue
            e["target_condition"] = f"{tc} (target as measured: catheterised PVR <100 mL, i.e. the inverse of retention)"
            ch.add("pocus_bladder_volume",
                   f"restated the target of estimate [{i}]: the study's positive state is a "
                   f"post-void residual BELOW 100 mL, the inverse of this record's question")

    # 7. abdominal rigidity ---------------------------------------------------------
    rec = rec_for("exam_abdominal_rigidity_guarding")
    if opts.rigidity == "label":
        for i, e in enumerate(rec.get("estimates", [])):
            tc = e.get("target_condition", "")
            if tc.endswith("(pediatric)"):
                ch.skipped.append(f"exam_abdominal_rigidity_guarding[{i}]: already labelled")
                continue
            e["target_condition"] = f"{tc} (pediatric)"
            ch.add("exam_abdominal_rigidity_guarding",
                   f"labelled estimate [{i}] pediatric - the only numbers under this adult "
                   f"abdominal-pain record come from a cohort of median age 11.9 years")
    else:
        n = len(rec.get("estimates", []))
        if n:
            rec["estimates"] = []
            rec["evidence_status"] = "not_quantified"
            ch.add("exam_abdominal_rigidity_guarding",
                   f"dropped all {n} estimates and set evidence_status to not_quantified - the "
                   f"evidence is pediatric (median age 11.9 y) and this record is retrieved for "
                   f"adults; extractor-A reached the same conclusion independently")

    # 8. palpitations before syncope ------------------------------------------------
    rec = rec_for("hx_palpitations_before_syncope")
    if opts.palpitations == "rewrite":
        if rec["interpretation"].get("positive_finding") == PALPITATIONS_POSITIVE:
            ch.skipped.append("hx_palpitations_before_syncope: prose already rewritten")
        else:
            rec["interpretation"]["positive_finding"] = PALPITATIONS_POSITIVE
            ch.add("hx_palpitations_before_syncope",
                   "rewrote interpretation.positive_finding - it asserted that palpitations raise "
                   "concern for arrhythmic syncope while the record's only estimate is LR+ 0.74, "
                   "which argues the other way; the new text leads with the pooled result and "
                   "presents the EGSYS +4 weighting as the convention it disagrees with")
    else:
        if rec.get("estimates"):
            rec["estimates"] = []
            rec["evidence_status"] = "not_quantified"
            ch.add("hx_palpitations_before_syncope",
                   "dropped the single estimate and set evidence_status to not_quantified - LR+ 0.74 "
                   "under a rule-in interpretation was the direction defect; extractor-B reached "
                   "not_quantified independently")

    # stamp ------------------------------------------------------------------------
    for rid, lines in ch.per_record.items():
        rec = out[rid]
        stamp = "\n".join(f"[owner fix] {l}" for l in lines)
        prior = (rec.get("verification_notes") or "").strip()
        rec["verification_notes"] = f"{prior}\n{stamp}".strip()
        try:
            rec["record_version"] = int(rec.get("record_version", 1)) + 1
        except (TypeError, ValueError):
            rec["record_version"] = 2

    return {rid: r for rid, r in out.items() if rid in ch.per_record}, ch


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    ap.add_argument("--bladder", choices=("flip-a", "relabel"), default="flip-a")
    ap.add_argument("--rigidity", choices=("label", "drop"), default="label")
    ap.add_argument("--palpitations", choices=("rewrite", "drop"), default="rewrite")
    opts = ap.parse_args()

    changed, ch = apply_all(opts)

    for rid in sorted(changed):
        print(f"\n{rid}")
        for line in ch.per_record[rid]:
            print(f"  - {line}")
    for s in ch.skipped:
        print(f"\nskip: {s}")

    if not opts.apply:
        print(f"\n{len(changed)} record(s) would change. Dry run: nothing written.")
        print("Re-run with --apply to write.")
        return 0

    for rid, rec in changed.items():
        (VERIFIED / f"{rid}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {len(changed)} record(s)")

    errs, warns = validate_records(VERIFIED)
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
