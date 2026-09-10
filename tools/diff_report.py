"""Deterministic A/B packet diff for the red-team pass and the owner's verification queue.

  python tools/diff_report.py [--resolve] > records/diff_report.md
Per id: agreement status, numeric mismatches, missing quote/location, vocab violations, silent
computation, unresolved citations (with --resolve: live PubMed/Crossref lookup via tools/pubmed.py).
Suggested verification order: unresolved/mismatch first, then rce_backed agreements, then rest.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.validate import DIFFERENTIALS, PRESENTATIONS, TAGS  # noqa: E402

STATS = ("sensitivity", "specificity", "lr_positive", "lr_negative")


def load_packets() -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for f in sorted((ROOT / "records" / "extracted").glob("*__*.json")):
        rid, agent = f.stem.split("__", 1)
        try:
            out[rid][agent] = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            out[rid][agent] = {"_invalid": str(e)}
    return out


def _est_key(e: dict) -> str:
    return f"{e.get('target_condition','?')} | {e.get('population','?')[:40]} | {e.get('setting','?')}"


def _val(e: dict, k: str):
    v = e.get(k)
    return v.get("value") if isinstance(v, dict) else None


def compare(rid: str, packs: dict[str, dict], resolve: bool) -> dict:
    flags: list[str] = []
    agents = sorted(packs)
    for a in agents:
        p = packs[a]
        if "_invalid" in p:
            flags.append(f"INVALID JSON ({a}): {p['_invalid']}")
            continue
        cm = p.get("clinical_mapping", {})
        for x in cm.get("presentations", []):
            if x not in PRESENTATIONS:
                flags.append(f"VOCAB VIOLATION ({a}): presentation {x}")
        for x in cm.get("differentials", []):
            if x not in DIFFERENTIALS:
                flags.append(f"VOCAB VIOLATION ({a}): differential {x}")
        for x in cm.get("indication_tags", []):
            if x not in TAGS:
                flags.append(f"VOCAB VIOLATION ({a}): tag {x}")
        for i, e in enumerate(p.get("estimates", [])):
            numeric = any(_val(e, k) is not None for k in STATS)
            if numeric and (not e.get("quote") or not e.get("location")):
                flags.append(f"NO LOCATION ({a}): estimates[{i}] {_est_key(e)}")
            if numeric and _val(e, "sensitivity") and _val(e, "specificity") and _val(e, "lr_positive"):
                s, c, lr = _val(e, "sensitivity"), _val(e, "specificity"), _val(e, "lr_positive")
                if c < 1 and abs(s / (1 - c) - lr) / max(lr, 1e-6) < 0.03 and not e.get("computed"):
                    flags.append(f"SILENT COMPUTATION? ({a}): estimates[{i}] LR+ equals sens/(1-spec) but computed=false")
        for j, s in enumerate(p.get("sources", [])):
            if s.get("kind") in ("guideline", "consensus") and p.get("evidence_status") == "quantified":
                flags.append(f"SECONDARY SOURCE? ({a}): sources[{j}] kind={s['kind']} on a quantified record")
            if not (s.get("doi") or s.get("pmid")):
                flags.append(f"UNRESOLVABLE ({a}): sources[{j}] has no DOI/PMID")
            elif resolve:
                from tools.pubmed import doi_lookup, fetch

                try:
                    hit = fetch(str(s["pmid"])) if s.get("pmid") else doi_lookup(s["doi"])
                    if not hit.get("title"):
                        flags.append(f"FABRICATION SUSPECT ({a}): sources[{j}] resolves to nothing")
                    elif hit.get("authors"):
                        first = hit["authors"][0].split()[0].lower()
                        cit = str(s.get("citation", "")).lower()
                        if first and first not in cit:
                            flags.append(f"AUTHOR MISMATCH ({a}): sources[{j}] cites '{s.get('citation','')[:40]}' but PubMed first author is {hit['authors'][0]}")
                except Exception as ex:  # noqa: BLE001
                    flags.append(f"FABRICATION SUSPECT ({a}): sources[{j}] lookup failed: {str(ex)[:60]}")
        if p.get("identity", {}).get("type") == "pocus" and not p.get("safety_scope", {}).get("skill_assumption"):
            flags.append(f"SCOPE ({a}): pocus without skill_assumption")
    status = "single_packet" if len(agents) < 2 else "agree"
    if len(agents) >= 2 and all("_invalid" not in packs[a] for a in agents):
        a, b = (packs[x] for x in agents[:2])
        if a.get("evidence_status") != b.get("evidence_status"):
            flags.append(f"STATUS MISMATCH: {a.get('evidence_status')} vs {b.get('evidence_status')}")
            status = "disagree"
        ea = {_est_key(e): e for e in a.get("estimates", [])}
        eb = {_est_key(e): e for e in b.get("estimates", [])}
        for k in ea.keys() & eb.keys():
            for st in STATS:
                va, vb = _val(ea[k], st), _val(eb[k], st)
                if va is not None and vb is not None and abs(va - vb) > 0.02 * max(abs(va), abs(vb), 1e-6):
                    flags.append(f"NUMERIC MISMATCH: {st} {va} vs {vb} [{k}]")
                    status = "disagree"
        if ea.keys() != eb.keys():
            flags.append(f"ESTIMATE SET DIFFERS: A={len(ea)} B={len(eb)} (population split or omission)")
            if status == "agree":
                status = "partial"
        sa = {str(s.get("pmid") or s.get("doi")) for s in a.get("sources", [])}
        sb = {str(s.get("pmid") or s.get("doi")) for s in b.get("sources", [])}
        if sa.isdisjoint(sb):
            flags.append("SOURCES DISJOINT: no shared PMID/DOI between packets")
            if status == "agree":
                status = "partial"
    return {"id": rid, "agents": agents, "status": status, "flags": flags}


def cross_record_duplicates(packets: dict[str, dict[str, dict]]) -> dict[str, list[str]]:
    """Same PMID + same LR/sens value appearing under two different ids → probable composite credited twice."""
    seen: dict[tuple, set[str]] = defaultdict(set)
    for rid, packs in packets.items():
        for p in packs.values():
            srcs = p.get("sources", [])
            for e in p.get("estimates", []):
                si = e.get("source_index")
                if si is None or si >= len(srcs):
                    continue
                key_src = str(srcs[si].get("pmid") or srcs[si].get("doi") or "")
                for st in STATS:
                    v = _val(e, st)
                    if v is not None and key_src:
                        seen[(key_src, st, round(v, 3))].add(rid)
    out: dict[str, list[str]] = defaultdict(list)
    for (src, st, v), rids in seen.items():
        if len(rids) > 1:
            for r in rids:
                out[r].append(f"COMPOSITE DUPLICATE? {st}={v} from {src} also under {sorted(rids - {r})}")
    return out


def main() -> None:
    resolve = "--resolve" in sys.argv
    ids_meta = {}
    p = ROOT / "discriminator_ids.json"
    if p.exists():
        ids_meta = {e["id"]: e for e in json.loads(p.read_text())["ids"]}
    packets = load_packets()
    dups = cross_record_duplicates(packets)
    rows = [compare(rid, packs, resolve) for rid, packs in packets.items()]
    for r in rows:
        r["flags"].extend(dups.get(r["id"], []))

    def order(r: dict) -> tuple:
        hard = any(f.startswith(("FABRICATION", "NUMERIC MISMATCH", "INVALID", "STATUS MISMATCH")) for f in r["flags"])
        rce = ids_meta.get(r["id"], {}).get("expected_evidence") == "rce_backed"
        return (0 if hard else 1, 0 if r["status"] == "disagree" else 1, 0 if rce else 1, r["id"])

    rows.sort(key=order)
    n = len(rows)
    print("# Extraction diff report\n")
    print(f"{n} ids; {sum(r['status']=='agree' for r in rows)} agree, {sum(r['status']=='partial' for r in rows)} partial, "
          f"{sum(r['status']=='disagree' for r in rows)} disagree, {sum(r['status']=='single_packet' for r in rows)} single-packet.\n")
    print("## Suggested verification order\n")
    for i, r in enumerate(rows, 1):
        print(f"{i}. `{r['id']}` — {r['status']} — {len(r['flags'])} flag(s)")
    print("\n## Per-id detail\n")
    for r in rows:
        print(f"### {r['id']}  ({', '.join(r['agents'])}) — **{r['status']}**")
        for f in r["flags"]:
            print(f"- {f}")
        if not r["flags"]:
            print("- no flags")
        print()


if __name__ == "__main__":
    main()
