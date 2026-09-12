"""Build the per-case documents that back the iPad judging page (gate 3).

  python3 tools/seed_judging.py <run_dir> <out_dir>

One JSON per benchmark case, holding the case's one-liner and its blinded items in queue order.
The arm is NOT in these files: it lives only in the run's judging_key.json, which the page never
sees, so scoring stays blind. Written to files for batch upload to the artifact store; nothing is
seeded in the page itself.

Near-identical recommendations are grouped so the judge rates each distinct recommendation once and
the score applies to every arm that made it. That is labour saving with no judgement attached, and
it removes a real source of noise: the same recommendation scored "relevant" under one arm and
"marginal" under another would bias the comparison by the judge's own inconsistency. Grouping uses
the harness's own text-match threshold (eval.mapping), the same notion of "the same recommendation"
already used for target presence, so nothing new is being asserted about what counts as a match.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.mapping import overlap, tokens  # noqa: E402

THRESHOLD = 0.6  # eval.mapping's own bar for "the same item"; see target_text_matches


def _same(a: set[str], b: set[str]) -> bool:
    if not a or not b or len(a & b) < 2:
        return False
    return max(overlap(a, b), overlap(b, a)) >= THRESHOLD


def group_queue(run_dir: Path) -> "OrderedDict[str, dict]":
    """{case_id: {case_id, presentation, oneliner, groups: [{gid, uids, text, variants}]}}.

    Deterministic: items are ordered by uid hash before clustering, so the same queue always
    produces the same groups and the same gids -- which is what lets the puller reconstruct the
    grouping from the queue alone instead of trusting a seed directory.
    """
    queue = run_dir / "judging_queue.csv"
    if not queue.exists():
        raise SystemExit(f"no judging_queue.csv in {run_dir} - run eval.judging_export first")
    cases: "OrderedDict[str, dict]" = OrderedDict()
    with queue.open(newline="") as f:
        for row in csv.DictReader(f):
            c = cases.setdefault(row["case_id"], {
                "case_id": row["case_id"], "presentation": row["presentation"],
                "oneliner": row["input_oneliner"], "_rows": [],
            })
            c["_rows"].append(row)

    for c in cases.values():
        # uid order, not arm order: arriving grouped by arm would let a run of similar phrasing
        # give the arm away.
        rows = sorted(c.pop("_rows"), key=lambda r: r["item_uid"])
        toks = [tokens(r["item_text"]) for r in rows]
        taken = [False] * len(rows)
        groups = []
        for i, row in enumerate(rows):
            if taken[i]:
                continue
            taken[i] = True
            members = [row]
            for j in range(i + 1, len(rows)):
                if not taken[j] and _same(toks[i], toks[j]):
                    taken[j] = True
                    members.append(rows[j])
            # show the fullest phrasing as the item, the others as variants, so the judge can see
            # exactly what they are rating in one go
            members.sort(key=lambda r: -len(r["item_text"]))
            groups.append({
                "gid": row["item_uid"],
                "uids": [m["item_uid"] for m in members],
                "text": members[0]["item_text"],
                "variants": [m["item_text"] for m in members[1:]],
            })
        c["groups"] = groups
        c["n_groups"] = len(groups)
        c["n_items"] = sum(len(g["uids"]) for g in groups)
    return cases


def main(run_dir: Path, out_dir: Path) -> int:
    cases = group_queue(run_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = list(cases.values())
    for i, doc in enumerate(docs):
        doc["order"] = i
        (out_dir / f"{doc['case_id']}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    index = {
        "cases": [{"case_id": d["case_id"], "presentation": d["presentation"],
                   "n_groups": d["n_groups"], "n_items": d["n_items"], "order": d["order"]} for d in docs],
        "n_cases": len(docs),
        "n_groups": sum(d["n_groups"] for d in docs),
        "n_items": sum(d["n_items"] for d in docs),
        "run": run_dir.name,
    }
    (out_dir / "_index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(docs)} case documents to {out_dir}")
    print(f"{index['n_items']} queue items -> {index['n_groups']} judgements "
          f"({100 * (index['n_items'] - index['n_groups']) / index['n_items']:.0f}% fewer)")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(args[0]), Path(args[1])))
