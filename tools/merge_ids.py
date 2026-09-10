"""Merge partial id drafts into discriminator_ids.json, union-ing arrays on id collision."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["dyspnea", "chest_pain", "syncope", "palpitations", "edema", "hypotension", "aki",
         "dizziness", "ams", "abdominal_pain", "fever", "weakness"]


def merge(paths: list[Path]) -> dict:
    merged: dict[str, dict] = {}
    collisions = []
    for p in paths:
        for e in json.loads(p.read_text())["ids"]:
            i = e["id"]
            if i not in merged:
                merged[i] = {**e, "indication_tags": e.get("indication_tags", [])}
                continue
            m = merged[i]
            collisions.append(i)
            for k in ("presentations", "differentials", "indication_tags"):
                m[k] = sorted(set(m.get(k, [])) | set(e.get(k, [])))
            if len(e.get("anchor_source", "")) > len(m.get("anchor_source", "")):
                m["anchor_source"] = e["anchor_source"]
            m["priority"] = min(m.get("priority", 3), e.get("priority", 3))
            rank = {"rce_backed": 0, "likely_quantified": 1, "likely_not_quantified": 2}
            if rank[e["expected_evidence"]] < rank[m["expected_evidence"]]:
                m["expected_evidence"] = e["expected_evidence"]
            if e.get("type") != m.get("type"):
                print(f"TYPE CONFLICT {i}: {m.get('type')} vs {e.get('type')}", file=sys.stderr)

    def key(e: dict) -> tuple:
        first = min((ORDER.index(p) for p in e["presentations"] if p in ORDER), default=99)
        return (e["priority"], first, e["id"])

    ids = sorted(merged.values(), key=key)
    for e in ids:
        e["presentations"] = sorted(set(e["presentations"]), key=lambda p: ORDER.index(p) if p in ORDER else 99)
        e["differentials"] = sorted(set(e["differentials"]))
    return {
        "_note": "Discriminator id list for Bedside Brief. Owner-editable until freeze #1. Sorted by priority, then first presentation in cardiology-first order. See DECISIONS.md #3/#4.",
        "_collisions_merged": sorted(set(collisions)),
        "ids": ids,
    }


if __name__ == "__main__":
    out = merge([Path(p) for p in sys.argv[1:]])
    (ROOT / "discriminator_ids.json").write_text(json.dumps(out, indent=2) + "\n")
    by_type: dict[str, int] = {}
    for e in out["ids"]:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    print(f"wrote {len(out['ids'])} ids; by type {by_type}; merged collisions {len(out['_collisions_merged'])}")
