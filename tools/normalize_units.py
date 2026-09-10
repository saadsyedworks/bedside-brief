"""Enforce the store convention: sensitivity/specificity/prevalence are PROPORTIONS (0-1). LRs are ratios.
Values > 1 for those fields are divided by 100 and the change is appended to extraction_notes.
  python tools/normalize_units.py records/extracted
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

FIELDS = ("sensitivity", "specificity")


def normalize(path: Path) -> list[str]:
    r = json.loads(path.read_text())
    changed = []
    for i, e in enumerate(r.get("estimates", [])):
        for f in FIELDS:
            st = e.get(f)
            if isinstance(st, dict) and isinstance(st.get("value"), (int, float)) and st["value"] > 1:
                for k in ("value", "ci_low", "ci_high"):
                    if isinstance(st.get(k), (int, float)) and st[k] > 1:
                        st[k] = round(st[k] / 100, 4)
                changed.append(f"estimates[{i}].{f}")
        if isinstance(e.get("prevalence"), (int, float)) and e["prevalence"] > 1:
            e["prevalence"] = round(e["prevalence"] / 100, 4)
            changed.append(f"estimates[{i}].prevalence")
    if changed:
        r["extraction_notes"] = (r.get("extraction_notes", "") + " [units normalised to proportions by tools/normalize_units.py: " + ", ".join(changed) + "]").strip()
        path.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
    return changed


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "records/extracted")
    n = 0
    for p in sorted(d.glob("*.json")):
        c = normalize(p)
        if c:
            n += 1
            print(p.name, "->", ", ".join(c))
    print(f"normalised {n} files")
