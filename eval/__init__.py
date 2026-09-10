"""Bedside Brief evaluation harness (PLAN.md Phase 3-4).

Modules:
  cases          expand benchmark files into base / perturbation / noise inputs (freeze check)
  classify       deterministic bedside vs off-bedside classifier (rubric + DECISIONS #11, #18)
  item_parser    free text -> item list (numbers via bedside_brief.validate.scan_numbers, citations)
  arms           arm A (full pipeline), B (retrieval-only), C (generic LLM) -> ArmOutput JSON
  mapping        target -> record-id map, token matcher, proposed-map helper, library coverage
  metrics        every mechanical metric in evaluation_rubric.md (+ stratifications)
  judging_export / judging_import   blinded owner judging queue and merge-back
  error_analysis top failure modes of arm A
  report         tables + figure, every number annotated with its source path
  run_all        CLI orchestrator (resumable)

Nothing here modifies bedside_brief/ or benchmark/cases/. Only eval/runs/ and the PROPOSED
mapping file are written.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `python3 -m eval.run_all` from ROOT works either way; scripts run directly need this
    sys.path.insert(0, str(ROOT))
