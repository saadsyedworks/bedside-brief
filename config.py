"""Bedside Brief configuration. Keys come only from .env (never logged)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# --- LLM -------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1")
LLM_FALLBACK_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.0
LLM_SEED = 7  # same seed for parser, ranker, comparator arm C


def openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing from .env")
    return key


# --- Paths -------------------------------------------------------------------
RECORDS_EXTRACTED = ROOT / "records" / "extracted"
RECORDS_VERIFIED = ROOT / "records" / "verified"
RECORDS_REDTEAM = ROOT / "records" / "redteam"
BENCHMARK_CASES = ROOT / "benchmark" / "cases"
SCHEMA_PATH = ROOT / "discriminator_schema.json"
VOCAB_PATH = ROOT / "vocab.json"
IDS_PATH = ROOT / "discriminator_ids.json"
DB_PATH = ROOT / "bedside_brief.sqlite"
EVAL_RUNS = ROOT / "eval" / "runs"

# --- Card limits (DAY1_FREEZE.md) -------------------------------------------
MAX_ASK = 4
MAX_EXAMINE = 4
MAX_POCUS = 3
POCUS_ENABLED = False  # owner flips in DAY1_FREEZE.md; retrieval excludes pocus until True

# --- Retrieval / rendering ---------------------------------------------------
RENDER_TIERS = ("verified",)  # only verified records ever render

# Whether the ranker is shown each candidate's safety_scope.do_not_use_when. Every verified record
# carries one, so with it on the model weighs a contraindication for all ~23 candidates per case.
# Reported as an ablation: arm B shares the parser but does not rank, so it isolates ranking effects.
# Env override so a run can flip it without editing code: BB_RANKER_CONTRAINDICATIONS=0
RANKER_SHOWS_CONTRAINDICATIONS = os.environ.get("BB_RANKER_CONTRAINDICATIONS", "1") != "0"
MAX_DIFFERENTIALS = 6
