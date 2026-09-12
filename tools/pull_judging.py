"""Fill a run's judging_queue.csv from the scores the owner tapped on the iPad page.

  python3 tools/pull_judging.py <scores_dir> <run_dir> [--dry-run]

`scores_dir` is what `Artifact action=read_db collection=judging_scores out_dir=...` writes: one
JSON per case, {case_id, scores: {group_id: {r, f}}, at}. The page rates one group per distinct
recommendation, so each score is expanded to every queue row in that group -- the grouping is
recomputed from the queue by tools.seed_judging.group_queue, which is deterministic, rather than
trusted from a seed directory. Relevance comes from `r`; `safety` is
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.judging_export import RELEVANCE  # noqa: E402
from tools.seed_judging import group_queue  # noqa: E402

FIELDS = ("item_uid", "case_id", "presentation", "input_oneliner", "item_text", "relevance", "safety")


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

    # gid -> every queue row the judge's one tap covers
    expand: dict[str, str] = {}
    for case in group_queue(run_dir).values():
        for g in case["groups"]:
            for uid in g["uids"]:
                expand[uid] = g["gid"]

    rows = list(csv.DictReader(queue.open(newline="")))
    filled = flagged = bad = 0
    for row in rows:
        s = scores.get(expand.get(row["item_uid"], row["item_uid"]))
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
        # a "not an item" row is not a recommendation, so a safety verdict on it means nothing
        row["safety"] = "" if rel == "not an item" else ("flag" if s.get("f") else "no flag")
        filled += 1
        flagged += bool(s.get("f"))

    groups = len({expand.get(r["item_uid"], r["item_uid"]) for r in rows if r.get("relevance")})
    print(f"{filled} of {len(rows)} rows scored from {groups} judgements "
          f"({flagged} flagged, {bad} invalid, {len(rows) - filled - bad} still blank)")
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
