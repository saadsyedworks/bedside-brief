"""End-to-end brief: parse -> retrieve -> rank -> render_card -> validate_or_block."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import config
from bedside_brief import rank as rank_mod
from bedside_brief import retrieve as retrieve_mod
from bedside_brief.parser import parse_oneliner
from bedside_brief.render import render_card
from bedside_brief.validate import validate_or_block

log = logging.getLogger("bedside_brief.pipeline")


def brief(text: str, llm: Any, db_path: str | Path | None = None, limits: Any = config) -> dict[str, Any]:
    """Run the whole pipeline. `db_path` defaults to config.DB_PATH at call time."""
    db_path = Path(db_path or config.DB_PATH)
    parsed = parse_oneliner(text, llm)
    candidates = retrieve_mod.retrieve(parsed, db_path, pocus_enabled=limits.POCUS_ENABLED)
    log.info("retrieve: %d candidates (%d cross-presentation)", len(candidates), sum(c.cross_presentation for c in candidates))
    chosen = rank_mod.rank(parsed, candidates, llm, limits)
    records_by_id = {c.id: c.record for c in candidates}  # chosen ids are a subset of the candidates
    card = render_card(chosen, records_by_id, parsed, limits)
    card, result = validate_or_block(card, records_by_id)
    log.info(
        "card: %s validation_ok=%s violations=%d",
        {s: len(items) for s, items in card["sections"].items()}, result.ok, len(result.violations),
    )
    return {
        "parsed": parsed,
        "candidates": [c.id for c in candidates],
        "chosen": chosen,
        "card": card,
        "validation": {"ok": result.ok, "violations": list(result.violations), "bad_item_ids": list(result.bad_item_ids)},
    }
