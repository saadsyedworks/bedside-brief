"""LLM ranking under card limits, from candidate ids only.

The LLM sees, per candidate: id, title, type, changes_what, evidence badge. It never sees
estimates, numbers or citations: `candidate_summary` strips digits from every non-id field
and `_assert_no_numbers` raises if any numeric literal survives. Any id outside the
candidate set, or in the wrong section for its type, raises `RankerContainmentError`.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import config
from bedside_brief.render import strip_numbers
from bedside_brief.retrieve import SECTION_TYPES, Candidate
from bedside_brief.validate import scan_numbers

log = logging.getLogger("bedside_brief.rank")


class RankerContainmentError(ValueError):
    """The ranker returned an id not in the candidates, or in a section its type is not allowed in."""


class RankerNumberLeak(RuntimeError):
    """A numeric literal reached the candidate summary; the prompt must never carry estimates."""


_CHOICE = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "rationale"],
        "properties": {"id": {"type": "string"}, "rationale": {"type": "string"}},
    },
}
RANK_SCHEMA: dict[str, Any] = {
    "title": "card_choice",
    "type": "object",
    "additionalProperties": False,
    "required": ["ask", "examine", "pocus"],
    "properties": {"ask": _CHOICE, "examine": _CHOICE, "pocus": _CHOICE},
}


def candidate_summary(candidates: list[Candidate]) -> list[dict[str, str]]:
    """What the LLM is allowed to see per candidate. Digit-free except the id.

    `avoid_when` carries the record's own `safety_scope.do_not_use_when`. Until this was added the
    field existed only to be printed: a card could recommend standing a patient for orthostatic
    vitals whose supine pressure was already too low, and display the contraindication underneath
    it. The ranker is the one place that knows both the manoeuvre and the patient, so it is where
    the contraindication has to be read.
    """
    rows = []
    for c in candidates:
        rec = c.record
        row = {
            "id": c.id,
            "title": strip_numbers(rec["identity"]["title"]),
            "type": c.type,
            "changes_what": strip_numbers(rec["interpretation"]["changes_what"]),
            "evidence_status": rec["evidence_status"],
        }
        avoid = (rec.get("safety_scope") or {}).get("do_not_use_when")
        if avoid:
            row["avoid_when"] = strip_numbers(avoid)
        rows.append(row)
    _assert_no_numbers(rows)
    return rows


def _assert_no_numbers(rows: list[dict[str, str]]) -> None:
    # ensure_ascii=False matters: the default escapes non-ASCII, so an arrow in changes_what
    # serialises as "\u2192" and the scan reads 2192 as a leaked number.
    without_ids = json.dumps([{k: v for k, v in r.items() if k != "id"} for r in rows], ensure_ascii=False)
    leaked = scan_numbers(without_ids)
    if leaked:
        raise RankerNumberLeak(f"numbers leaked into candidate summary: {sorted(leaked)}")


def system_prompt(limits: Any) -> str:
    lines = [
        "You choose which bedside discriminators go on a ~20-second pre-encounter card for a hospitalist.",
        "You will receive a parsed one-liner and a list of candidate discriminators. Choose ONLY from the candidate ids given;",
        "any id not in the list is a hard failure. Put history-type candidates under 'ask'; exam- and functional-type",
        "candidates under 'examine'; pocus-type under 'pocus'.",
        f"Limits: at most {limits.MAX_ASK} in ask, at most {limits.MAX_EXAMINE} in examine, "
        + (f"at most {limits.MAX_POCUS} in pocus." if limits.POCUS_ENABLED else "and pocus must be an empty list."),
        "Order each section by how much the item would change the next action for THIS patient.",
        "A candidate may carry 'avoid_when': the condition under which that manoeuvre is unsafe or must not be",
        "attempted. If the patient as described meets it, do NOT choose that candidate, however well it fits the",
        "differential — pick the next best one instead. Judge it against the patient given, not a hypothetical one.",
        "For each chosen id write one short rationale sentence in plain words. Do not include any number, estimate,",
        "sensitivity, specificity, likelihood ratio, or citation in the rationale; the card renders evidence from the store itself.",
        "Reply with the JSON object only.",
    ]
    return "\n".join(lines)


def _parsed_summary(parsed: dict[str, Any]) -> dict[str, Any]:
    return {k: parsed.get(k) for k in ("chief_complaint", "presentation", "time_course", "modifiers", "differentials", "indication_tags", "missing_features")}


def _empty(limits: Any) -> dict[str, list[dict[str, str]]]:
    chosen: dict[str, list[dict[str, str]]] = {"ask": [], "examine": []}
    if limits.POCUS_ENABLED:
        chosen["pocus"] = []
    return chosen


def rank(parsed: dict[str, Any], candidates: list[Candidate], llm: Any, limits: Any = config) -> dict[str, list[dict[str, str]]]:
    """Return the render `chosen` contract: {"ask": [{"id", "rationale"}], "examine": [...], ("pocus": [...])}."""
    if not candidates:
        log.info("rank: no candidates; empty card")
        return _empty(limits)
    by_id = {c.id: c for c in candidates}
    user = json.dumps({"patient": _parsed_summary(parsed), "candidates": candidate_summary(candidates)}, indent=1)
    reply = llm.complete_json(system_prompt(limits), user, RANK_SCHEMA)

    caps = {"ask": limits.MAX_ASK, "examine": limits.MAX_EXAMINE, "pocus": limits.MAX_POCUS}
    chosen: dict[str, list[dict[str, str]]] = {}
    for section, types in SECTION_TYPES.items():
        items = reply.get(section) or []
        if section == "pocus" and not limits.POCUS_ENABLED:
            if items:
                log.warning("rank: pocus disabled; dropping %d pocus choice(s)", len(items))
            continue
        kept: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in items:
            rid = item["id"]
            cand = by_id.get(rid)
            if cand is None:
                raise RankerContainmentError(f"{section}/{rid}: not a candidate id")
            if cand.type not in types:
                raise RankerContainmentError(f"{section}/{rid}: type {cand.type!r} not allowed in section")
            if rid in seen:
                continue
            seen.add(rid)
            kept.append({"id": rid, "rationale": strip_numbers(item.get("rationale"))})
        if len(kept) > caps[section]:
            log.warning("rank: %s over limit (%d > %d); truncating in LLM order", section, len(kept), caps[section])
        chosen[section] = kept[: caps[section]]
    log.info("rank: chosen %s", {s: len(v) for s, v in chosen.items()})
    return chosen
