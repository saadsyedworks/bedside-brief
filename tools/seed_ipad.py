"""Build the per-id documents that back the iPad verification page.

  python3 tools/seed_ipad.py <out_dir>

One JSON per discriminator id: both packets trimmed to what a verifier reads (technique,
interpretation, every estimate with its quote, location and a tappable source link), plus the
deterministic diff status/flags, any red-team lines mentioning the id, and the queue order.
Written to files so they can be batch-uploaded to the artifact store; nothing is seeded in the page.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.diff_report import compare, load_packets  # noqa: E402

# DECISIONS #35: one packet is not_quantified while the other carries a real, located number.
QUICKWIN = {
    "exam_chest_hyperresonance": "A",
    "exam_kussmaul_sign": "A",
    "exam_line_exit_site_erythema_purulence": "A",
    "exam_tense_distended_abdomen_iah": "A",
    "hx_steroid_exposure_withdrawal": "B",
    "hx_recent_antibiotics_new_diarrhea": "B",
}


def _stat(est: dict, key: str) -> dict | None:
    v = est.get(key)
    if not isinstance(v, dict) or v.get("value") is None:
        return None
    return {"value": v["value"], "ci_low": v.get("ci_low"), "ci_high": v.get("ci_high")}


def _source_link(src: dict) -> str:
    if src.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{src['pmid']}/"
    if src.get("doi"):
        return f"https://doi.org/{src['doi']}"
    return ""


def trim(packet: dict) -> dict:
    srcs = packet.get("sources", [])
    ests = []
    for e in packet.get("estimates", []):
        i = e.get("source_index")
        src = srcs[i] if isinstance(i, int) and 0 <= i < len(srcs) else {}
        ests.append({
            "target_condition": e.get("target_condition", ""),
            "population": e.get("population", ""),
            "setting": e.get("setting", ""),
            "reference_standard": e.get("reference_standard", ""),
            "prevalence": e.get("prevalence"),
            "sensitivity": _stat(e, "sensitivity"),
            "specificity": _stat(e, "specificity"),
            "lr_positive": _stat(e, "lr_positive"),
            "lr_negative": _stat(e, "lr_negative"),
            "evidence_level": e.get("evidence_level", ""),
            "computed": bool(e.get("computed")),
            "computed_from": e.get("computed_from", ""),
            "quote": e.get("quote", ""),
            "location": e.get("location", ""),
            "citation": src.get("citation", ""),
            "kind": src.get("kind", ""),
            "link": _source_link(src),
        })
    tech, interp, safety = packet.get("technique", {}), packet.get("interpretation", {}), packet.get("safety_scope", {})
    return {
        "evidence_status": packet.get("evidence_status", ""),
        "how": tech.get("how", ""),
        "contraindications": tech.get("contraindications", ""),
        "positive_finding": interp.get("positive_finding", ""),
        "negative_finding": interp.get("negative_finding", ""),
        "changes_what": interp.get("changes_what", ""),
        "pitfalls": interp.get("pitfalls", ""),
        "skill_assumption": safety.get("skill_assumption", ""),
        "notes": packet.get("extraction_notes", ""),
        "estimates": ests,
        "n_sources": len(srcs),
    }


def redteam_lines(rid: str) -> list[str]:
    out: list[str] = []
    for f in sorted((ROOT / "records" / "redteam").glob("*.md")):
        for line in f.read_text().splitlines():
            if rid in line and line.strip() and not line.strip().startswith("#"):
                out.append(re.sub(r"\s+", " ", line.strip())[:400])
    return out[:12]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ids_meta = {e["id"]: e for e in json.loads((ROOT / "discriminator_ids.json").read_text())["ids"]}
    packets = load_packets()
    rows = [compare(rid, packs, resolve=False) for rid, packs in packets.items()]

    def order(r: dict) -> tuple:
        meta = ids_meta.get(r["id"], {})
        hard = any(f.startswith(("FABRICATION", "NUMERIC MISMATCH", "INVALID", "STATUS MISMATCH")) for f in r["flags"])
        return (0 if r["id"] in QUICKWIN else 1,
                0 if hard else 1,
                0 if r["status"] == "disagree" else 1,
                0 if meta.get("expected_evidence") == "rce_backed" else 1,
                r["id"])

    rows.sort(key=order)
    for n, r in enumerate(rows, 1):
        rid = r["id"]
        meta = ids_meta.get(rid, {})
        packs = packets[rid]
        doc = {
            "id": rid,
            "order": n,
            "title": meta.get("title", rid),
            "type": meta.get("type", ""),
            "presentations": meta.get("presentations", []),
            "differentials": meta.get("differentials", []),
            "expected_evidence": meta.get("expected_evidence", ""),
            "anchor_source": meta.get("anchor_source", ""),
            "status": r["status"],
            "flags": r["flags"][:20],
            "redteam": redteam_lines(rid),
            "quickwin": QUICKWIN.get(rid),
            "A": trim(packs.get("extractor-A", {})),
            "B": trim(packs.get("extractor-B", {})),
        }
        (out_dir / f"{rid}.json").write_text(json.dumps(doc, ensure_ascii=False))
    index = [{
        "id": r["id"],
        "order": n,
        "title": ids_meta.get(r["id"], {}).get("title", r["id"])[:110],
        "type": ids_meta.get(r["id"], {}).get("type", ""),
        "status": r["status"],
        "flags": len(r["flags"]),
        "quickwin": QUICKWIN.get(r["id"]),
        "rce": ids_meta.get(r["id"], {}).get("expected_evidence") == "rce_backed",
    } for n, r in enumerate(rows, 1)]
    (out_dir / "_index.json").write_text(json.dumps({"queue": index, "n": len(index), "target": 60}, ensure_ascii=False))
    print(f"index: {len((out_dir / '_index.json').read_bytes()) // 1024} KB")
    print(f"wrote {len(rows)} docs to {out_dir}")
    sizes = [len((out_dir / f'{r["id"]}.json').read_bytes()) for r in rows]
    print(f"mean {sum(sizes)//len(sizes)} bytes, max {max(sizes)}, total {sum(sizes)//1024} KB")
    print("first 8:", [r["id"] for r in rows[:8]])


if __name__ == "__main__":
    main(Path(sys.argv[1]))
