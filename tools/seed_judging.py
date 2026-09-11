"""Build the per-case documents that back the iPad judging page (gate 3).

  python3 tools/seed_judging.py <run_dir> <out_dir>

One JSON per benchmark case, holding the case's one-liner and its blinded items in queue order.
The arm is NOT in these files: it lives only in the run's judging_key.json, which the page never
sees, so scoring stays blind. Written to files for batch upload to the artifact store; nothing is
seeded in the page itself.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path


def build(run_dir: Path) -> list[dict]:
    queue = run_dir / "judging_queue.csv"
    if not queue.exists():
        raise SystemExit(f"no judging_queue.csv in {run_dir} — run eval.judging_export first")
    cases: "OrderedDict[str, dict]" = OrderedDict()
    with queue.open(newline="") as f:
        for row in csv.DictReader(f):
            c = cases.setdefault(row["case_id"], {
                "case_id": row["case_id"],
                "presentation": row["presentation"],
                "oneliner": row["input_oneliner"],
                "items": [],
            })
            c["items"].append({"uid": row["item_uid"], "text": row["item_text"]})
    # Items arrive grouped by arm, which would let a judge infer the arm from a run of similar
    # phrasing. Interleaving by uid is deterministic (same order every rebuild) and breaks the run.
    for c in cases.values():
        c["items"].sort(key=lambda i: i["uid"])
        c["n_items"] = len(c["items"])
    return list(cases.values())


def main(run_dir: Path, out_dir: Path) -> int:
    docs = build(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, doc in enumerate(docs):
        doc["order"] = i
        (out_dir / f"{doc['case_id']}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    index = {"cases": [{"case_id": d["case_id"], "presentation": d["presentation"],
                        "n_items": d["n_items"], "order": d["order"]} for d in docs],
             "n_cases": len(docs), "n_items": sum(d["n_items"] for d in docs),
             "run": run_dir.name}
    (out_dir / "_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(docs)} case documents ({index['n_items']} items) to {out_dir}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(args[0]), Path(args[1])))
