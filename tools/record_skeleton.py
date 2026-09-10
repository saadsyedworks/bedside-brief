"""Emit a schema-shaped skeleton for one discriminator id so extractors fill only evidence fields.

  python tools/record_skeleton.py exam_jvp_elevated A   -> prints JSON skeleton with agent_id "extractor-A"
identity / clinical_mapping come from discriminator_ids.json (vocab-guaranteed); extractors may ADD
differentials/tags only from vocab.json and must not remove the seeded ones.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def skeleton(rec_id: str, agent: str) -> dict:
    ids = {e["id"]: e for e in json.loads((ROOT / "discriminator_ids.json").read_text())["ids"]}
    e = ids[rec_id]
    sk = {
        "identity": {"id": e["id"], "title": e["title"], "type": e["type"], "bedside": True},
        "clinical_mapping": {
            "presentations": e["presentations"],
            "syndromes": [],
            "differentials": e["differentials"],
            "indication_tags": e.get("indication_tags", []),
        },
        "technique": {"how": "", "prerequisites": "", "contraindications": ""},
        "interpretation": {"positive_finding": "", "negative_finding": "", "pitfalls": "", "changes_what": ""},
        "estimates": [],
        "evidence_status": "not_quantified",
        "sources": [],
        "safety_scope": {"do_not_use_when": "", "escalation_warning": "", "interobserver_note": ""},
        "tier": "extracted",
        "extraction_notes": "",
        "agent_id": f"extractor-{agent}",
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verified_by": None,
        "verified_at": None,
        "verification_notes": "",
        "record_version": 1,
    }
    if e["type"] == "pocus":
        sk["safety_scope"]["skill_assumption"] = ""
    sk["_anchor_source"] = e.get("anchor_source", "")
    sk["_expected_evidence"] = e.get("expected_evidence", "")
    return sk


if __name__ == "__main__":
    print(json.dumps(skeleton(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "A"), indent=2))
