"""Deterministic retrieval over the SQLite index. No LLM, no randomness.

Key: parsed `differentials` (primary, weighted) and `indication_tags` (secondary boost).
`presentation` is a filter: in-presentation candidates come first; cross-presentation
matches are appended after them, flagged, because DAY1_FREEZE says cross-presentation
retrieval is expected. `pocus` records are excluded unless enabled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import config
from bedside_brief import store

TAG_BOOST = 0.25
SECTION_TYPES: dict[str, frozenset[str]] = {
    "ask": frozenset({"history"}),
    "examine": frozenset({"exam", "functional"}),
    "pocus": frozenset({"pocus"}),
}


@dataclass(frozen=True)
class Candidate:
    id: str
    type: str
    score: float
    matched_differentials: tuple[str, ...]
    matched_tags: tuple[str, ...]
    cross_presentation: bool
    record: dict[str, Any] = field(compare=False, repr=False)


def _weights(parsed: dict[str, Any]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for d in parsed.get("differentials") or []:
        dx = d.get("dx")
        if dx:
            weights[dx] = weights.get(dx, 0.0) + float(d.get("weight", 1.0))
    return weights


def retrieve(
    parsed: dict[str, Any],
    index_db: str | Path | None = None,
    pocus_enabled: bool | None = None,
) -> list[Candidate]:
    """Candidates sorted by (in-presentation first, -score, id). Same input -> same output."""
    pocus_enabled = config.POCUS_ENABLED if pocus_enabled is None else pocus_enabled
    weights = _weights(parsed)
    if not weights:
        return []
    tags = set(parsed.get("indication_tags") or [])
    presentation = parsed.get("presentation")

    in_presentation: list[Candidate] = []
    cross: list[Candidate] = []
    for record in store.records_matching(weights, index_db):
        if record.get("tier") not in config.RENDER_TIERS:
            continue  # only verified records are ever surfaced
        rtype = record["identity"]["type"]
        if rtype == "pocus" and not pocus_enabled:
            continue
        mapping = record["clinical_mapping"]
        matched_dx = tuple(sorted(d for d in mapping["differentials"] if d in weights))
        matched_tags = tuple(sorted(t for t in mapping.get("indication_tags", []) if t in tags))
        score = round(sum(weights[d] for d in matched_dx) + TAG_BOOST * len(matched_tags), 6)
        is_cross = presentation not in mapping["presentations"]
        candidate = Candidate(
            id=record["identity"]["id"], type=rtype, score=score,
            matched_differentials=matched_dx, matched_tags=matched_tags,
            cross_presentation=is_cross, record=record,
        )
        (cross if is_cross else in_presentation).append(candidate)

    def order(c: Candidate) -> tuple[float, str]:
        return (-c.score, c.id)

    return sorted(in_presentation, key=order) + sorted(cross, key=order)


def retrieve_fixed_order(
    parsed: dict[str, Any],
    index_db: str | Path | None = None,
    pocus_enabled: bool | None = None,
    limits: Any = config,
) -> dict[str, list[Candidate]]:
    """Eval arm B: retrieval order as-is, no LLM ranking, truncated to the card limits per section."""
    pocus_enabled = config.POCUS_ENABLED if pocus_enabled is None else pocus_enabled
    candidates = retrieve(parsed, index_db, pocus_enabled)
    caps = {"ask": limits.MAX_ASK, "examine": limits.MAX_EXAMINE, "pocus": limits.MAX_POCUS}
    sections: dict[str, list[Candidate]] = {}
    for section, types in SECTION_TYPES.items():
        if section == "pocus" and not pocus_enabled:
            continue
        sections[section] = [c for c in candidates if c.type in types][: caps[section]]
    return sections


def to_chosen(sections: dict[str, list[Candidate]]) -> dict[str, list[dict[str, str]]]:
    """Adapt fixed-order sections to the `chosen` contract consumed by render.render_card."""
    return {section: [{"id": c.id, "rationale": ""} for c in cands] for section, cands in sections.items()}
