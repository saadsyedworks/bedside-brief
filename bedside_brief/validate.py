"""Number scanning and card validation.

Non-negotiable: every number on a rendered card must exist in a linked verified record.
`scan_numbers` / `normalise_number` are the single source of truth for what counts as a
number, and are used on BOTH sides (record inventory in store.py, card scan here), so
the comparison is exact by construction.
"""
from __future__ import annotations

import copy
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterator

import config

log = logging.getLogger("bedside_brief.validate")

# Integers, decimals, leading-dot decimals; ranges ("0.7–0.9") and "LR+ 4.2" fall out of
# the tokeniser naturally because dashes, "+", and spaces are not part of a match.
_NUM_RE = re.compile(r"(?<![\w.])\.\d+|\d+(?:\.\d+)?")

# Keys the validator never scans: produced by this module itself, never by an LLM.
_UNSCANNED_CARD_KEYS = frozenset({"blocked"})


def normalise_number(token: str | int | float) -> str:
    """Canonical text for a number: "85%" -> "85", ".85" -> "0.85", "2.10" -> "2.1", 2.0 -> "2"."""
    s = str(token).strip().rstrip("%").strip().lstrip("+")
    if s.startswith("."):
        s = "0" + s
    try:
        d = Decimal(s)
    except InvalidOperation:
        return s
    if not d.is_finite():
        return s
    return format(d.normalize(), "f")


def scan_numbers(text: str) -> set[str]:
    """All numeric literals in `text`, normalised."""
    return {normalise_number(m) for m in _NUM_RE.findall(text or "")}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    violations: list[str] = field(default_factory=list)
    bad_item_ids: list[str] = field(default_factory=list)
    bad_card_fields: list[str] = field(default_factory=list)  # card-level keys (ask_first, chief_complaint...) carrying foreign numbers


def _leaf_strings(node: Any) -> Iterator[str]:
    """Every string (and number, as text) reachable in a nested card structure."""
    if isinstance(node, bool) or node is None:
        return
    if isinstance(node, (int, float)):
        yield normalise_number(node)
    elif isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _leaf_strings(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from _leaf_strings(value)


def _numbers_in(node: Any) -> set[str]:
    found: set[str] = set()
    for s in _leaf_strings(node):
        found |= scan_numbers(s)
    return found


def validate_card(card: dict[str, Any], records_by_id: dict[str, dict[str, Any]]) -> ValidationResult:
    """Check a rendered card against the records it links.

    Per item: the item's id must be a verified-tier record, and every number in the item's
    text must be in `store.numbers_in_record` of that record. Card-level text outside items
    may only contain numbers present in at least one linked record.
    """
    from bedside_brief import store  # lazy: store imports scan_numbers from this module

    violations: list[str] = []
    bad_ids: list[str] = []
    allowed_union: set[str] = set()

    for section, items in (card.get("sections") or {}).items():
        for item in items:
            rid = item.get("id")
            record = records_by_id.get(rid)
            if record is None or record.get("tier") not in config.RENDER_TIERS:
                violations.append(f"{section}/{rid}: not a verified record")
                bad_ids.append(rid)
                continue
            allowed = store.numbers_in_record(record)
            allowed_union |= allowed
            extra = sorted(_numbers_in(item) - allowed)
            if extra:
                violations.append(f"{section}/{rid}: numbers not in record: {extra}")
                bad_ids.append(rid)

    outside = {k: v for k, v in card.items() if k != "sections" and k not in _UNSCANNED_CARD_KEYS}
    bad_fields = sorted(k for k, v in outside.items() if _numbers_in(v) - allowed_union)
    extra = sorted(_numbers_in(outside) - allowed_union)
    if extra:
        violations.append(f"card: numbers outside items not in any linked record: {extra} (fields {bad_fields})")

    for v in violations:
        log.warning("validator: %s", v)
    return ValidationResult(ok=not violations, violations=violations, bad_item_ids=bad_ids, bad_card_fields=bad_fields)


def block(card: dict[str, Any], result: ValidationResult) -> dict[str, Any]:
    """Replacement card with the violating items AND violating card-level fields (e.g. `ask_first`)
    removed, plus a `blocked` note. The result always re-validates clean: nothing is re-generated."""
    blocked = copy.deepcopy(card)
    bad = set(result.bad_item_ids)
    sections = blocked.get("sections") or {}
    for section, items in sections.items():
        sections[section] = [item for item in items if item.get("id") not in bad]
    removed_fields = [k for k in result.bad_card_fields if k in blocked]
    for k in removed_fields:
        del blocked[k]
    blocked["blocked"] = {
        "removed": sorted(bad),
        "removed_fields": removed_fields,
        "violations": list(result.violations),
        "note": "Some items were withheld because their text failed the evidence check.",
    }
    return blocked


def validate_or_block(card: dict[str, Any], records_by_id: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], ValidationResult]:
    """Convenience: return (card, result) where card is the original if ok else the blocked one."""
    result = validate_card(card, records_by_id)
    return (card if result.ok else block(card, result)), result
