"""Top failure modes of arm A with examples -> error_analysis.md (rubric: "top 5 failure modes of A").

Modes counted: missing must_have targets (by presentation), pipeline errors, blocked items
(validator withheld), ask-first false positives / negatives, unsupported quantitative claims,
should_not_recommend hits, empty cards, brevity failures. Ranked by count; top 5 first.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def analyse(metrics: dict[str, Any], arm: str = "A") -> dict[str, Any]:
    rows = [r for r in metrics["per_case"] if r["arm"] == arm]
    am = metrics["arms"].get(arm, {})
    modes: dict[str, dict[str, Any]] = {}

    missing_by_pres: dict[str, Counter] = defaultdict(Counter)
    missing_examples: list[dict[str, Any]] = []
    for r in rows:
        for t in r["missing_must_have"]:
            missing_by_pres[r["presentation"]][t] += 1
            if len(missing_examples) < 12:
                missing_examples.append({"case_id": r["case_id"], "target": t})
    n_missing = sum(sum(c.values()) for c in missing_by_pres.values())
    modes["missing_must_have_targets"] = {
        "count": n_missing, "unit": "targets",
        "by_presentation": {p: {"missing": sum(c.values()), "top": c.most_common(3)} for p, c in sorted(missing_by_pres.items())},
        "examples": missing_examples,
    }
    errs = [r for r in rows if r["error"]]
    modes["pipeline_errors"] = {"count": len(errs), "unit": "cases", "examples": [{"case_id": r["case_id"], "error": r["error"]} for r in errs[:8]]}
    blocked = [r for r in rows if r["blocked_items"]]
    modes["validator_blocked_items"] = {"count": sum(len(r["blocked_items"]) for r in blocked), "unit": "items",
                                        "examples": [{"case_id": r["case_id"], "blocked": r["blocked_items"]} for r in blocked[:8]]}
    fp = [r["case_id"] for r in rows if r["ask_first"] and not r["ask_first_expected"]]
    fn = [r["case_id"] for r in rows if not r["ask_first"] and r["ask_first_expected"]]
    modes["ask_first_false_positives"] = {"count": len(fp), "unit": "cases", "examples": fp[:12]}
    modes["ask_first_false_negatives"] = {"count": len(fn), "unit": "cases", "examples": fn[:12]}
    ucr = am.get("unsupported_claim_rate") or {}
    modes["unsupported_quantitative_claims"] = {"count": ucr.get("unsupported", 0), "unit": "numbers", "examples": (ucr.get("examples") or [])[:8]}
    snr = am.get("should_not_recommend") or {}
    modes["should_not_recommend_hits"] = {"count": snr.get("cases_hit", 0), "unit": "cases", "examples": (snr.get("examples") or [])[:8]}
    empty = [r["case_id"] for r in rows if r["items"] == 0 and not r["error"]]
    modes["empty_cards"] = {"count": len(empty), "unit": "cases", "examples": empty[:12]}
    brev = [r["case_id"] for r in rows if not r["brevity_pass"]]
    modes["brevity_failures"] = {"count": len(brev), "unit": "cases", "examples": brev[:12]}

    ranked = sorted(modes.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    return {"arm": arm, "cases": len(rows), "top5": [k for k, _ in ranked[:5]], "modes": dict(ranked)}


def markdown(ea: dict[str, Any]) -> str:
    lines = [f"# Error analysis — arm {ea['arm']} ({ea['cases']} case inputs)", "", "## Top 5 failure modes", ""]
    for i, k in enumerate(ea["top5"], 1):
        m = ea["modes"][k]
        lines.append(f"{i}. **{k.replace('_', ' ')}** — {m['count']} {m['unit']}")
    lines += ["", "## Detail", ""]
    for k, m in ea["modes"].items():
        lines.append(f"### {k.replace('_', ' ')} ({m['count']} {m['unit']})")
        if "by_presentation" in m:
            for p, v in m["by_presentation"].items():
                tops = "; ".join(f"{t} ×{n}" for t, n in v["top"])
                lines.append(f"- {p}: {v['missing']} missing — {tops}")
        for ex in m.get("examples") or []:
            lines.append(f"- {json.dumps(ex, ensure_ascii=False) if isinstance(ex, dict) else ex}")
        if not m.get("examples") and "by_presentation" not in m:
            lines.append("- none")
        lines.append("")
    return "\n".join(lines)


def write(metrics: dict[str, Any], run_dir: str | Path, arm: str = "A") -> Path:
    ea = analyse(metrics, arm)
    run_dir = Path(run_dir)
    (run_dir / "error_analysis.json").write_text(json.dumps(ea, indent=1))
    p = run_dir / "error_analysis.md"
    p.write_text(markdown(ea))
    return p
