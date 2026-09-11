"""Turn decisions made in the iPad verifier into records/verified/*.json.

  python3 tools/pull_decisions.py <decisions_dir> [--dry-run]

`decisions_dir` is what `Artifact action=read_db ... out_dir=...` writes: one JSON per decision,
{id, action, base, exclude[], notes, at}. For every `promote` this rebuilds the chosen extraction
packet minus the excluded estimates, stamps tier/verified_by/verified_at/verification_notes, and
writes it only if it passes the same checks the desktop app enforces. Rejections are recorded in
records/rejected/. Nothing is promoted that the owner did not promote.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate import validate_records  # noqa: E402

EXTRACTED = ROOT / "records" / "extracted"
VERIFIED = ROOT / "records" / "verified"
REJECTED = ROOT / "records" / "rejected"


STAT_FIELDS = ("sensitivity", "specificity", "lr_positive", "lr_negative")
STAT_LABEL = {"sensitivity": "sensitivity", "specificity": "specificity",
              "lr_positive": "LR+", "lr_negative": "LR-"}


def apply_edits(rec: dict, base: str, edits: dict) -> tuple[list[str], list[str]]:
    """Apply the owner's per-estimate corrections in place.

    A corrected point estimate invalidates the stored confidence interval, so the bounds are cleared
    rather than left attached to a number they no longer describe. Every change is written into
    verification_notes, and a corrected value that no longer appears in its own quote is warned about.
    """
    lines, warnings = [], []
    ests = rec.get("estimates", [])
    for key in sorted(edits):
        side, _, idx = key.partition(":")
        if side != base or not idx.isdigit():
            continue
        i = int(idx)
        if i >= len(ests):
            warnings.append(f"correction for estimates[{i}] but the packet has {len(ests)}")
            continue
        est, ed = ests[i], edits[key]
        target = est.get("target_condition", f"estimates[{i}]")
        for field in STAT_FIELDS:
            if field not in ed:
                continue
            new_value = ed[field]
            was = est.get(field)
            old_value = was.get("value") if isinstance(was, dict) else None
            if old_value is not None and float(old_value) == float(new_value):
                continue
            est[field] = {"value": new_value, "ci_low": None, "ci_high": None}
            lines.append(f"[owner correction] {target}: {STAT_LABEL[field]} "
                         f"{old_value if old_value is not None else 'absent'} -> {new_value} "
                         f"(confidence interval cleared)")
            if est.get("quote") and str(new_value) not in str(est["quote"]):
                warnings.append(f"estimates[{i}] {STAT_LABEL[field]}={new_value} does not appear in its quote")
        if ed.get("note"):
            lines.append(f"[owner note] {target}: {ed['note'].strip()}")
    return lines, warnings


def build(decision: dict) -> tuple[str, dict | None, str]:
    rid = decision["id"]
    base = decision.get("base")
    src = EXTRACTED / f"{rid}__extractor-{base}.json"
    if not src.exists():
        return rid, None, f"no packet for extractor-{base}"
    rec = json.loads(src.read_text())
    edit_lines, edit_warnings = apply_edits(rec, base, decision.get("edits") or {})
    for w in edit_warnings:
        print(f"WARN  {rid}: {w}")
    exclude = set(decision.get("exclude") or [])
    kept = [e for i, e in enumerate(rec.get("estimates", [])) if i not in exclude]
    if exclude and kept:
        # source_index values must still point at the right entry in sources[]
        used = sorted({e["source_index"] for e in kept if isinstance(e.get("source_index"), int)})
        remap = {old: new for new, old in enumerate(used)}
        rec["sources"] = [rec["sources"][i] for i in used]
        for e in kept:
            if isinstance(e.get("source_index"), int):
                e["source_index"] = remap[e["source_index"]]
    # When every estimate is excluded the record becomes not_quantified, and the spec still requires
    # it to cite the guideline or consensus source supporting the manoeuvre — so keep sources intact.
    rec["estimates"] = kept
    if not kept and rec.get("evidence_status") != "not_quantified":
        rec["evidence_status"] = "not_quantified"
    rec["tier"] = "verified"
    rec["verified_by"] = "owner"
    rec["verified_at"] = decision.get("at")
    notes = [(decision.get("notes") or "").strip()] if (decision.get("notes") or "").strip() else []
    rec["verification_notes"] = "\n".join(notes + edit_lines)
    rec["record_version"] = 1
    prior = VERIFIED / f"{rid}.json"
    if prior.exists():
        try:
            rec["record_version"] = int(json.loads(prior.read_text()).get("record_version", 1)) + 1
        except Exception:  # noqa: BLE001
            pass
    rec.pop("_anchor_source", None)
    rec.pop("_expected_evidence", None)
    detail = f"from extractor-{base}, {len(kept)} of {len(kept) + len(exclude)} estimates kept"
    if edit_lines:
        detail += f", {sum(1 for l in edit_lines if l.startswith('[owner correction]'))} value(s) corrected"
    return rid, rec, detail


def main(src_dir: Path, dry: bool) -> int:
    decisions = []
    for f in sorted(src_dir.rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            print(f"SKIP {f.name}: unreadable ({e})")
            continue
        if isinstance(d, dict) and d.get("id") and d.get("action"):
            decisions.append(d)
    if not decisions:
        print(f"No decisions found in {src_dir}")
        return 1

    VERIFIED.mkdir(parents=True, exist_ok=True)
    REJECTED.mkdir(parents=True, exist_ok=True)
    promoted, rejected, skipped, failed = [], [], [], []

    for d in decisions:
        act = d["action"]
        if act == "promote":
            rid, rec, why = build(d)
            if rec is None:
                failed.append(f"{rid}: {why}")
                continue
            if not dry:
                (VERIFIED / f"{rid}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
            promoted.append(f"{rid} ({why})")
        elif act == "reject":
            rid = d["id"]
            if not dry:
                (REJECTED / f"{rid}.json").write_text(json.dumps(
                    {"id": rid, "reason": d.get("notes", ""), "rejected_at": d.get("at")},
                    indent=2, ensure_ascii=False) + "\n")
            rejected.append(rid)
        else:
            skipped.append(d["id"])

    errs, warns = validate_records(VERIFIED)
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)

    print(f"\npromoted {len(promoted)} · rejected {len(rejected)} · skipped {len(skipped)} · failed {len(failed)}")
    for line in promoted:
        print("  +", line)
    for line in failed:
        print("  !", line)
    if dry:
        print("\n(dry run: nothing written)")
    return 1 if errs or failed else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(Path(args[0]), "--dry-run" in sys.argv))
