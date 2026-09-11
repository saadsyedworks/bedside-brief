"""Fill a run's judging_queue.csv from the scores the owner tapped on the iPad page.

  python3 tools/pull_judging.py <scores_dir> <run_dir> [--dry-run]

`scores_dir` is what `Artifact action=read_db collection=judging_scores out_dir=...` writes: one
JSON per case, {case_id, scores: {item_uid: {r, f}}, at}. Relevance comes from `r`; `safety` is
written as "flag" where `f` is true and "no flag" for every other scored item, because the page
asks for a flag only when there is something to flag -- an unflagged item that was scored for
relevance was seen and judged safe, which is not the same as unscored.

Rows with no relevance are left blank so eval.judging_import reports them as unscored rather than
counting them. Nothing is invented: an item the owner never touched stays empty.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

FIELDS = ("item_uid", "case_id", "presentation", "input_oneliner", "item_text", "relevance", "safety")
RELEVANCE = ("relevant", "marginal", "irrelevant")


def load_scores(scores_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted(scores_dir.rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            print(f"SKIP {f.name}: unreadable ({e})")
            continue
        for uid, s in (d.get("scores") or {}).items():
            if isinstance(s, dict):
                out[uid] = s
    return out


def main(scores_dir: Path, run_dir: Path, dry: bool) -> int:
    queue = run_dir / "judging_queue.csv"
    if not queue.exists():
        print(f"no judging_queue.csv in {run_dir}")
        return 1
    scores = load_scores(scores_dir)
    if not scores:
        print(f"no scores found in {scores_dir}")
        return 1

    rows = list(csv.DictReader(queue.open(newline="")))
    filled = flagged = bad = 0
    for row in rows:
        s = scores.get(row["item_uid"])
        if not s:
            continue
        rel = str(s.get("r") or "").strip().lower()
        if not rel:
            continue
        if rel not in RELEVANCE:
            print(f"BAD  {row['item_uid']}: relevance={rel!r} (left blank)")
            bad += 1
            continue
        row["relevance"] = rel
        row["safety"] = "flag" if s.get("f") else "no flag"
        filled += 1
        flagged += bool(s.get("f"))

    print(f"{filled} of {len(rows)} rows scored ({flagged} flagged, {bad} invalid, "
          f"{len(rows) - filled - bad} still blank)")
    if dry:
        print("(dry run: nothing written)")
        return 0
    with queue.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: row.get(k, "") for k in FIELDS} for row in rows)
    print(f"wrote {queue}")
    print(f"next: python3 -m eval.judging_import --run-dir {run_dir}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(args[0]), Path(args[1]), "--dry-run" in sys.argv))
