"""Every MECHANICAL metric in evaluation_rubric.md, per arm, plus the owner-ruled stratifications.

  bedside share             modes default / ecg_bedside / mar_offbedside   (DECISIONS #18 rulings 4 + ECG sensitivity)
  target recall must_have   overall AND stratified quantified vs not_quantified by the mapped verified record (ruling 3)
  target recall all, library coverage, evidence fidelity (A/B), unsupported quantitative claim rate (all arms),
  perturbation responsiveness, noise stability, brevity, not-quantified share, should_not_recommend hit rate,
  ask-first correctness.

Target presence (DECISIONS #13): ANY mapped id on the card, else deterministic text match
(eval.mapping.target_text_matches) so arm C - which has no record ids - is scored by the same rule.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

import config
from bedside_brief import store
from eval.arms import ARMS, ArmOutput
from eval.cases import CaseInput, Target, by_base
from eval.classify import MODES, is_bedside, section_for
from eval.mapping import jaccard, library_coverage, overlap, phrase_matches, target_text_matches, tokens

log = logging.getLogger("eval.metrics")

QUANTIFIED_STATUSES = frozenset({"quantified", "partially_quantified"})
STRATA = ("quantified", "not_quantified", "unmapped")
FALLBACK_JACCARD_CHANGE = 0.2


def _ratio(n: int | float, d: int | float) -> float | None:
    return (n / d) if d else None


def _item_key(item: dict[str, Any]) -> str:
    return item.get("record_id") or " ".join(sorted(tokens(item.get("text", ""))))


# --- target presence -----------------------------------------------------------------------
def target_present(target: Target, out: ArmOutput, titles: dict[str, str]) -> str | None:
    """'id' | 'text' | 'title' | None — how the target was found on the output."""
    ids = set(out.record_ids)
    if any(i in ids for i in target.mapped_ids):
        return "id"
    for it in out.items:
        if target_text_matches(target.item, it["text"]):
            return "text"
    for rid in target.mapped_ids:
        title = titles.get(rid)
        if title and any(phrase_matches(title, it["text"]) for it in out.items):
            return "title"
    return None


def target_stratum(target: Target, records_by_id: dict[str, dict[str, Any]]) -> str:
    statuses = [records_by_id[i]["evidence_status"] for i in target.mapped_ids if i in records_by_id and records_by_id[i].get("tier") == "verified"]
    if not statuses:
        return "unmapped"
    return "quantified" if any(s in QUANTIFIED_STATUSES for s in statuses) else "not_quantified"


# --- per-item helpers ------------------------------------------------------------------------
def _backing_numbers(item: dict[str, Any], records_by_id: dict[str, dict[str, Any]], titles: dict[str, str], cache: dict[str, set[str]]) -> set[str]:
    """Numbers a verified record vouches for: the item's own record (A/B) or verified records whose
    title matches the item text (C)."""
    rid = item.get("record_id")
    if rid:
        return cache.setdefault(rid, store.numbers_in_record(records_by_id[rid])) if rid in records_by_id else set()
    backing: set[str] = set()
    for vid, title in titles.items():
        if phrase_matches(title, item["text"]) or phrase_matches(item["text"], title):
            backing |= cache.setdefault(vid, store.numbers_in_record(records_by_id[vid]))
    return backing


# A prohibition is written short ("NSAIDs for muscle pain"), a card item long, so the asymmetric
# overlap below is what decides the match. At three content tokens, two generic ones in common clear
# 0.6: that is how "Muscle pain/weakness, prolonged immobilization or exertion, dark cola-colored
# urine" -- correct rhabdomyolysis screening in a found-down patient -- was scored as recommending
# NSAIDs, on `muscle` and `pain`, with `nsaid` nowhere in the item. Below four tokens there is no room
# for a partial match to mean anything, so require the prohibition to be wholly present.
_SNR_SHORT = 4


def _snr_hit(item_text: str, snr: str) -> bool:
    a, b = tokens(item_text), tokens(snr)
    if len(a & b) < 2:
        return False
    if len(b) < _SNR_SHORT:
        return b <= a
    return max(overlap(a, b), overlap(b, a)) >= 0.6


def _brevity(out: ArmOutput, limits: Any) -> tuple[bool, dict[str, int]]:
    caps = {"ask": limits.MAX_ASK, "examine": limits.MAX_EXAMINE, "pocus": limits.MAX_POCUS}
    counts: Counter[str] = Counter()
    for it in out.items:
        sec = it.get("section") if it.get("section") in caps else section_for(it.get("category", ""))
        counts[sec or "other"] += 1
    total_cap = limits.MAX_ASK + limits.MAX_EXAMINE + (limits.MAX_POCUS if limits.POCUS_ENABLED else 0)
    ok = len(out.items) <= total_cap and all(counts[s] <= caps[s] for s in caps)
    return ok, dict(counts)


# --- main -----------------------------------------------------------------------------------
def compute_metrics(
    cases: list[CaseInput],
    outputs: dict[str, dict[str, ArmOutput]],
    records_by_id: dict[str, dict[str, Any]],
    limits: Any = config,
    extracted_ids: set[str] | None = None,
) -> dict[str, Any]:
    verified = {i: r for i, r in records_by_id.items() if r.get("tier") == "verified"}
    titles = {i: r["identity"]["title"] for i, r in verified.items()}
    all_verified_numbers: set[str] = set()
    num_cache: dict[str, set[str]] = {}
    for vid, rec in verified.items():
        num_cache[vid] = store.numbers_in_record(rec)
        all_verified_numbers |= num_cache[vid]
    cases_by_id = {c.case_id: c for c in cases}
    grouped = by_base(cases)

    result: dict[str, Any] = {
        "store": {
            "verified": len(verified),
            "extracted": len(extracted_ids) if extracted_ids is not None else None,
            "not_quantified": sum(r["evidence_status"] == "not_quantified" for r in verified.values()),
            "not_quantified_share": _ratio(sum(r["evidence_status"] == "not_quantified" for r in verified.values()), len(verified)),
            "evidence_status_counts": dict(Counter(r["evidence_status"] for r in verified.values())),
            "library_coverage": library_coverage(cases, set(verified)),
        },
        "cases": {
            "inputs": len(cases), "base": sum(c.variant == "base" for c in cases),
            "perturbation_pairs": sum(c.variant == "p1" for c in cases), "noise_variants": sum(c.variant == "n1" for c in cases),
            "underspecified": sorted(c.case_id for c in cases if c.underspecified_expected),
        },
        "arms": {},
        "per_case": [],
        "notes": [],
    }

    for arm in ARMS:
        outs = outputs.get(arm) or {}
        if not outs:
            continue
        m: dict[str, Any] = {"n_outputs": len(outs), "n_errors": sum(1 for o in outs.values() if o.error), "errors": {}}
        items_total = 0
        bedside_counts = {mode: 0 for mode in MODES}
        bedside_per_case = {mode: [] for mode in MODES}
        cat_counts: Counter[str] = Counter()
        mh = {"present": 0, "total": 0, "by": Counter(), "strata": {s: {"present": 0, "total": 0} for s in STRATA}}
        allt = {"present": 0, "total": 0}
        fid = {"matched": 0, "displayed": 0}
        claims = {"unsupported": 0, "claims": 0, "perf_unsupported": 0, "perf_claims": 0, "any_unsupported": 0, "examples": []}
        brev = {"pass": 0, "cards": 0, "items": []}
        snr = {"cases_hit": 0, "cases": 0, "items_hit": 0, "examples": []}
        askf = {"correct": 0, "cases": 0, "false_positives": [], "false_negatives": []}

        for case_id, out in sorted(outs.items()):
            case = cases_by_id.get(case_id)
            if case is None:
                continue
            if out.error:
                m["errors"][case_id] = out.error
            n_items = len(out.items)
            items_total += n_items
            for mode in MODES:
                b = sum(is_bedside(it["category"], mode) for it in out.items)
                bedside_counts[mode] += b
                if n_items:
                    bedside_per_case[mode].append(b / n_items)
            cat_counts.update(it["category"] for it in out.items)
            # target recall
            missing_mh: list[str] = []
            mh_present = 0
            for t in case.targets:
                how = target_present(t, out, titles)
                allt["total"] += 1
                allt["present"] += bool(how)
                if t.must_have:
                    stratum = target_stratum(t, records_by_id)
                    mh["total"] += 1
                    mh["strata"][stratum]["total"] += 1
                    if how:
                        mh["present"] += 1
                        mh_present += 1
                        mh["by"][how] += 1
                        mh["strata"][stratum]["present"] += 1
                    else:
                        missing_mh.append(t.item)
            # numbers
            unsupported_case = 0
            for it in out.items:
                nums = set(it.get("numeric_claims") or [])
                perf = set(it.get("performance_claims") or [])
                if it.get("record_id"):
                    backing = _backing_numbers(it, records_by_id, titles, num_cache)
                    fid["displayed"] += len(nums)
                    fid["matched"] += len(nums & backing)
                else:
                    backing = _backing_numbers(it, records_by_id, titles, num_cache)
                claims["claims"] += len(nums)
                bad = nums - backing
                claims["unsupported"] += len(bad)
                unsupported_case += len(bad)
                claims["perf_claims"] += len(perf)
                claims["perf_unsupported"] += len(perf - backing)
                claims["any_unsupported"] += len(nums - all_verified_numbers)
                if bad and len(claims["examples"]) < 25:
                    claims["examples"].append({"case_id": case_id, "text": it["text"][:160], "unsupported": sorted(bad)})
            # brevity
            ok, counts = _brevity(out, limits)
            brev["cards"] += 1
            brev["pass"] += ok
            brev["items"].append(n_items)
            # should_not_recommend
            snr["cases"] += 1
            hit_items = [(it["text"], s) for it in out.items for s in case.should_not_recommend if _snr_hit(it["text"], s)]
            if hit_items:
                snr["cases_hit"] += 1
                snr["items_hit"] += len({t for t, _ in hit_items})
                if len(snr["examples"]) < 25:
                    snr["examples"].append({"case_id": case_id, "item": hit_items[0][0][:160], "should_not_recommend": hit_items[0][1]})
            # ask-first
            askf["cases"] += 1
            if out.ask_first == case.underspecified_expected:
                askf["correct"] += 1
            elif out.ask_first:
                askf["false_positives"].append(case_id)
            else:
                askf["false_negatives"].append(case_id)
            result["per_case"].append({
                "arm": arm, "case_id": case_id, "base_case_id": case.base_case_id, "variant": case.variant, "presentation": case.presentation,
                "error": out.error, "items": n_items, "bedside_items": sum(is_bedside(it["category"], "default") for it in out.items),
                "must_have_present": mh_present, "must_have_total": len(case.must_have_targets), "missing_must_have": missing_mh,
                "unsupported_claims": unsupported_case, "brevity_pass": ok, "section_counts": counts,
                "snr_hit": bool(hit_items), "ask_first": out.ask_first, "ask_first_expected": case.underspecified_expected,
                "blocked_items": list(out.blocked_items or []),
            })

        # pairs: perturbation + noise
        pert = {"pairs": 0, "score_sum": 0.0, "explicit_pairs": 0, "fallback_pairs": 0, "per_pair": {}}
        noise = {"pairs": 0, "per_pair": {}}
        for base_id, variants in sorted(grouped.items()):
            base_out = outs.get(base_id)
            if base_out is None:
                continue
            p1 = variants.get("p1")
            if p1 and p1.case_id in outs:
                p1_out = outs[p1.case_id]
                if p1.expected_change_targets:
                    hits = 0
                    for e in p1.expected_change_targets:
                        if isinstance(e, int):
                            if 0 <= e < len(p1.targets):
                                hits += bool(target_present(p1.targets[e], p1_out, titles))
                        else:
                            rid = str(e)
                            hits += rid in p1_out.record_ids or (rid in titles and any(phrase_matches(titles[rid], it["text"]) for it in p1_out.items))
                    score = hits / len(p1.expected_change_targets)
                    pert["explicit_pairs"] += 1
                    how = "explicit"
                else:
                    change = 1.0 - jaccard(map(_item_key, base_out.items), map(_item_key, p1_out.items))
                    score = 1.0 if change >= FALLBACK_JACCARD_CHANGE else 0.0
                    pert["fallback_pairs"] += 1
                    how = f"fallback_jaccard_change={change:.2f}"
                pert["pairs"] += 1
                pert["score_sum"] += score
                pert["per_pair"][base_id] = {"score": score, "how": how}
            n1 = variants.get("n1")
            if n1 and n1.case_id in outs:
                j = jaccard(map(_item_key, base_out.items), map(_item_key, outs[n1.case_id].items))
                noise["pairs"] += 1
                noise["per_pair"][base_id] = round(j, 3)
        if pert["fallback_pairs"]:
            note = (f"arm {arm}: perturbation responsiveness used the Jaccard-change fallback (>= {FALLBACK_JACCARD_CHANGE}) for "
                    f"{pert['fallback_pairs']} of {pert['pairs']} pairs because no expected_change_targets were given")
            log.warning(note)
            result["notes"].append(note)

        m.update({
            "items_total": items_total,
            "items_per_case_mean": _ratio(items_total, len(outs)),
            "category_counts": dict(cat_counts),
            "unclassified_items": cat_counts.get("unclassified", 0),
            "bedside_share": {
                mode: {"bedside": bedside_counts[mode], "items": items_total, "share": _ratio(bedside_counts[mode], items_total),
                       "per_case_mean": _ratio(sum(bedside_per_case[mode]), len(bedside_per_case[mode]))}
                for mode in MODES
            },
            # Pre-specified (DECISIONS #24), an unclassified item counts as not-bedside, so it sits in the
            # denominator above. That is only fair if unclassified means "a recommendation we could not
            # place". In free-text arms much of it is formatting the item parser could not help splitting
            # out -- section headers, citation lines, commentary on the item above -- and those are not
            # recommendations at all, so counting them penalises the arm for its prose style rather than
            # for what it told the clinician to do. This sensitivity analysis drops them from both sides;
            # the primary metric above is unchanged.
            "bedside_share_classified": {
                mode: {"bedside": bedside_counts[mode],
                       "items": items_total - cat_counts.get("unclassified", 0),
                       "share": _ratio(bedside_counts[mode], items_total - cat_counts.get("unclassified", 0))}
                for mode in MODES
            },
            "target_recall_must_have": {
                "present": mh["present"], "total": mh["total"], "recall": _ratio(mh["present"], mh["total"]), "found_by": dict(mh["by"]),
                "strata": {s: {**v, "recall": _ratio(v["present"], v["total"])} for s, v in mh["strata"].items()},
            },
            "target_recall_all": {**allt, "recall": _ratio(allt["present"], allt["total"])},
            "evidence_fidelity": ({**fid, "fidelity": _ratio(fid["matched"], fid["displayed"])} if arm in ("A", "B") else None),
            "unsupported_claim_rate": {
                "unsupported": claims["unsupported"], "claims": claims["claims"], "rate": _ratio(claims["unsupported"], claims["claims"]),
                "performance_only": {"unsupported": claims["perf_unsupported"], "claims": claims["perf_claims"], "rate": _ratio(claims["perf_unsupported"], claims["perf_claims"])},
                "any_verified_record": {"unsupported": claims["any_unsupported"], "claims": claims["claims"], "rate": _ratio(claims["any_unsupported"], claims["claims"])},
                "examples": claims["examples"],
            },
            "perturbation_responsiveness": {
                "pairs": pert["pairs"], "rate": _ratio(pert["score_sum"], pert["pairs"]), "explicit_pairs": pert["explicit_pairs"],
                "fallback_pairs": pert["fallback_pairs"], "per_pair": pert["per_pair"],
            },
            "noise_stability": {
                "pairs": noise["pairs"], "jaccard_mean": _ratio(sum(noise["per_pair"].values()), noise["pairs"]),
                "jaccard_min": min(noise["per_pair"].values()) if noise["per_pair"] else None, "per_pair": noise["per_pair"],
            },
            "brevity": {"pass": brev["pass"], "cards": brev["cards"], "pass_rate": _ratio(brev["pass"], brev["cards"]),
                        "items_per_card_mean": _ratio(sum(brev["items"]), len(brev["items"])), "items_per_card_max": max(brev["items"] or [0])},
            "should_not_recommend": {"cases_hit": snr["cases_hit"], "cases": snr["cases"], "case_hit_rate": _ratio(snr["cases_hit"], snr["cases"]),
                                     "items_hit": snr["items_hit"], "items": items_total, "item_hit_rate": _ratio(snr["items_hit"], items_total), "examples": snr["examples"]},
            "ask_first": {"correct": askf["correct"], "cases": askf["cases"], "accuracy": _ratio(askf["correct"], askf["cases"]),
                          "false_positives": askf["false_positives"], "false_negatives": askf["false_negatives"]},
        })
        result["arms"][arm] = m
    return result


# --- output ---------------------------------------------------------------------------------
def _fmt(x: Any, pct: bool = True) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{100 * x:.1f}%" if pct else f"{x:.3f}"
    return str(x)


def _row(label: str, arms: list[str], get, pct: bool = True) -> str:
    return f"| {label} | " + " | ".join(_fmt(get(a), pct) for a in arms) + " |"


def metrics_markdown(m: dict[str, Any]) -> str:
    arms = list(m["arms"])
    A = m["arms"]
    lines = ["# Mechanical metrics", "", f"Inputs: {m['cases']['inputs']} ({m['cases']['base']} base, {m['cases']['perturbation_pairs']} perturbation pairs, "
             f"{m['cases']['noise_variants']} noise variants). Store: {m['store']['verified']} verified"
             + (f" of {m['store']['extracted']} extracted" if m['store']['extracted'] is not None else "")
             + f"; not-quantified share {_fmt(m['store']['not_quantified_share'])}; library coverage {_fmt(m['store']['library_coverage']['coverage'])} "
             f"({m['store']['library_coverage']['mapped_to_verified']}/{m['store']['library_coverage']['targets']} targets).", "",
             "| Metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    lines.append(_row("Outputs (errors)", arms, lambda a: f"{A[a]['n_outputs']} ({A[a]['n_errors']})"))
    lines.append(_row("Items per case (mean)", arms, lambda a: A[a]["items_per_case_mean"], pct=False))
    for mode in MODES:
        lines.append(_row(f"Bedside share [{mode}]", arms, lambda a, mode=mode: A[a]["bedside_share"][mode]["share"]))
    lines.append(_row("Bedside share [excl. unclassified]", arms, lambda a: A[a]["bedside_share_classified"]["default"]["share"]))
    lines.append(_row("Unclassified items", arms, lambda a: A[a]["unclassified_items"]))
    lines.append(_row("Target recall must_have", arms, lambda a: A[a]["target_recall_must_have"]["recall"]))
    for s in STRATA:
        lines.append(_row(f"  must_have recall [{s}] (n)", arms, lambda a, s=s: f"{_fmt(A[a]['target_recall_must_have']['strata'][s]['recall'])} ({A[a]['target_recall_must_have']['strata'][s]['total']})"))
    lines.append(_row("Target recall all", arms, lambda a: A[a]["target_recall_all"]["recall"]))
    lines.append(_row("Evidence fidelity (A/B)", arms, lambda a: (A[a]["evidence_fidelity"] or {}).get("fidelity")))
    lines.append(_row("Unsupported quantitative claim rate", arms, lambda a: A[a]["unsupported_claim_rate"]["rate"]))
    lines.append(_row("  performance numbers only", arms, lambda a: A[a]["unsupported_claim_rate"]["performance_only"]["rate"]))
    lines.append(_row("  vs any verified record (lenient)", arms, lambda a: A[a]["unsupported_claim_rate"]["any_verified_record"]["rate"]))
    lines.append(_row("Perturbation responsiveness", arms, lambda a: A[a]["perturbation_responsiveness"]["rate"]))
    lines.append(_row("  pairs explicit / fallback", arms, lambda a: f"{A[a]['perturbation_responsiveness']['explicit_pairs']} / {A[a]['perturbation_responsiveness']['fallback_pairs']}"))
    lines.append(_row("Noise stability (Jaccard mean)", arms, lambda a: A[a]["noise_stability"]["jaccard_mean"], pct=False))
    lines.append(_row("Brevity pass rate", arms, lambda a: A[a]["brevity"]["pass_rate"]))
    lines.append(_row("should_not_recommend case hit rate", arms, lambda a: A[a]["should_not_recommend"]["case_hit_rate"]))
    lines.append(_row("Ask-first correctness", arms, lambda a: A[a]["ask_first"]["accuracy"]))
    if m["notes"]:
        lines += ["", "Notes:"] + [f"- {n}" for n in m["notes"]]
    return "\n".join(lines) + "\n"


def write_metrics(m: dict[str, Any], run_dir: str | Path) -> tuple[Path, Path]:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    pj, pm = run_dir / "metrics.json", run_dir / "metrics.md"
    pj.write_text(json.dumps(m, indent=1, sort_keys=True))
    pm.write_text(metrics_markdown(m))
    return pj, pm
