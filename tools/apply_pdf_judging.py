"""Turn the completed paper judging packet into the per-case score documents.

  python3 tools/apply_pdf_judging.py <rows.json> <run_dir> <out_dir> [--changes changes.json]

`rows.json` comes from tools/read_judging_pdf.py: one entry per printed row, in document order.
`changes.json` is {"<row number 1-N>": "<grade>"} for rows the owner re-graded afterwards, numbered
over the *affected subset* the re-grade sheet listed -- so this also needs that same subset, which it
recomputes rather than trusts (see tools/regrade_packet.affected).

Writes one JSON per case in the shape tools/pull_judging.py reads, so the paper route and the tablet
route converge on the same code path and the same merge.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.regrade_packet import affected, case_order  # noqa: E402
from tools.seed_judging import group_queue  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rows")
    ap.add_argument("run_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--changes", default=None)
    args = ap.parse_args()

    rows = json.loads(Path(args.rows).read_text())
    run_dir = Path(args.run_dir)
    cases = group_queue(run_dir)
    order = case_order(run_dir)

    # row -> (case, gid), in the document's own order
    placed: list[tuple[str, str]] = []
    for cid in order:
        for g in cases[cid]["groups"]:
            placed.append((cid, g["gid"]))
    if len(placed) != len(rows):
        raise SystemExit(f"{len(rows)} rows in the document, {len(placed)} groups in the run")

    scores: dict[str, dict[str, dict]] = {cid: {} for cid in order}
    for (cid, gid), row in zip(placed, rows):
        grade = next((t for t in row["ticked"] if t != "flag"), None)
        if not grade:
            continue
        entry: dict[str, object] = {"r": grade}
        if "flag" in row["ticked"]:
            entry["f"] = True
        scores[cid][gid] = entry

    changed = 0
    if args.changes:
        # the re-grade sheet numbered the affected subset 1..N; recompute that subset identically
        subset = affected(rows, run_dir, order)
        flat = [(cid, it["rank"]) for cid, items in subset.items() for it in items]
        edits = json.loads(Path(args.changes).read_text())
        for key, grade in edits.items():
            n = int(key)
            if not 1 <= n <= len(flat):
                raise SystemExit(f"change {n} is outside the {len(flat)} affected rows")
            cid, rank = flat[n - 1]
            gid = cases[cid]["groups"][rank - 1]["gid"]
            before = scores[cid][gid]["r"]
            if before != grade:
                scores[cid][gid]["r"] = grade
                changed += 1
        print(f"applied {changed} re-grades of {len(edits)} given, over {len(flat)} affected rows")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for cid, sc in scores.items():
        (out / f"{cid}.json").write_text(json.dumps(
            {"case_id": cid, "scores": sc, "at": "paper packet"}, indent=2) + "\n")
    total = sum(len(s) for s in scores.values())
    print(f"wrote {len(scores)} case documents, {total} graded rows, to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
