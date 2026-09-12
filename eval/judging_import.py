"""Merge the owner's scored judging_queue.csv back with judging_key.json -> per-arm relevance / safety.

Writes judged_metrics.json + judged_metrics.md into the run dir. Unscored rows are reported,
not silently dropped; invalid labels raise so a typo cannot skew an arm.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from eval.judging_export import JUDGED_RELEVANCE, RELEVANCE, SAFETY


def _norm(v: str) -> str:
    return (v or "").strip().lower().replace("_", " ")


def merge(csv_path: str | Path, key_path: str | Path) -> dict[str, Any]:
    key = json.loads(Path(key_path).read_text())["items"]
    per_arm: dict[str, dict[str, Any]] = {}
    unscored: list[str] = []
    unknown: list[str] = []
    invalid: list[str] = []
    with Path(csv_path).open(newline="") as f:
        for row in csv.DictReader(f):
            uid = row["item_uid"]
            if uid not in key:
                unknown.append(uid)
                continue
            arm = key[uid]["arm"]
            m = per_arm.setdefault(arm, {"scored": 0, "relevance": Counter(), "safety": Counter(), "cases": set()})
            rel, saf = _norm(row.get("relevance", "")), _norm(row.get("safety", ""))
            if not rel and not saf:
                unscored.append(uid)
                continue
            if rel and rel not in RELEVANCE:
                invalid.append(f"{uid}: relevance={row.get('relevance')!r}")
            if saf and saf not in SAFETY:
                invalid.append(f"{uid}: safety={row.get('safety')!r}")
            m["scored"] += 1
            m["cases"].add(key[uid]["case_id"])
            if rel:
                m["relevance"][rel] += 1
            if saf:
                m["safety"][saf] += 1
    if invalid:
        raise ValueError("invalid judging labels: " + "; ".join(invalid[:10]))
    out: dict[str, Any] = {"arms": {}, "unscored": len(unscored), "unknown_uids": unknown}
    for arm, m in sorted(per_arm.items()):
        # Items the judge marked "not an item" are not recommendations, so they leave the
        # relevance denominator; both denominators are reported so the effect is visible.
        n_graded = sum(m["relevance"][k] for k in JUDGED_RELEVANCE)
        n_all, n_saf = sum(m["relevance"].values()), sum(m["safety"].values())
        out["arms"][arm] = {
            "scored_items": m["scored"], "cases": len(m["cases"]),
            "relevance": {k: m["relevance"][k] for k in RELEVANCE},
            "graded_items": n_graded, "not_an_item": m["relevance"]["not an item"],
            "relevant_share": (m["relevance"]["relevant"] / n_graded) if n_graded else None,
            "relevant_or_marginal_share": ((m["relevance"]["relevant"] + m["relevance"]["marginal"]) / n_graded) if n_graded else None,
            "relevant_share_all_scored": (m["relevance"]["relevant"] / n_all) if n_all else None,
            "safety": {k: m["safety"][k] for k in SAFETY}, "safety_flag_rate": (m["safety"]["flag"] / n_saf) if n_saf else None,
        }
    return out


def markdown(j: dict[str, Any]) -> str:
    arms = list(j["arms"])
    f = lambda x: "—" if x is None else f"{100 * x:.1f}%"  # noqa: E731
    lines = ["# Judged metrics (single author-reviewer, blinded to arm)", "", "| Metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    lines.append("| Scored items | " + " | ".join(str(j["arms"][a]["scored_items"]) for a in arms) + " |")
    lines.append("| Not a recommendation | " + " | ".join(str(j["arms"][a]["not_an_item"]) for a in arms) + " |")
    lines.append("| Graded items | " + " | ".join(str(j["arms"][a]["graded_items"]) for a in arms) + " |")
    lines.append("| Relevant share | " + " | ".join(f(j["arms"][a]["relevant_share"]) for a in arms) + " |")
    lines.append("| Relevant share (all scored) | " + " | ".join(f(j["arms"][a]["relevant_share_all_scored"]) for a in arms) + " |")
    lines.append("| Relevant or marginal share | " + " | ".join(f(j["arms"][a]["relevant_or_marginal_share"]) for a in arms) + " |")
    lines.append("| Safety flag rate | " + " | ".join(f(j["arms"][a]["safety_flag_rate"]) for a in arms) + " |")
    lines.append(f"\nUnscored rows: {j['unscored']}; unknown uids: {len(j['unknown_uids'])}\n")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--scored", default=None, help="scored CSV (default: <run-dir>/judging_queue.csv)")
    a = ap.parse_args(argv)
    run_dir = Path(a.run_dir)
    j = merge(a.scored or run_dir / "judging_queue.csv", run_dir / "judging_key.json")
    (run_dir / "judged_metrics.json").write_text(json.dumps(j, indent=1, sort_keys=True))
    (run_dir / "judged_metrics.md").write_text(markdown(j))
    print(markdown(j))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
