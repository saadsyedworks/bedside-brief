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

# Which candidates arrive at the ranker carrying their safety_scope.do_not_use_when:
#   "off"      none. Best measured performance (recall 71.0%, perturbation 69.4%) but it recommends
#              standing a patient at supine 88/54 -- 3 violations of 108 inputs, all hypotension_002.
#   "all"      every candidate. The only configuration measured at zero violations, at the cost of
#              ten points of perturbation responsiveness: all 153 records carry a do_not_use_when,
#              so the model weighs a caveat against all ~23 candidates per case and turns cautious.
#   "relevant" only those whose contraindication names a state the patient's own stated
#              measurements put them in (bedside_brief.patient). SHIPPED (owner decision,
#              DECISIONS #51): zero violations at recall 70.0% / perturbation 65.3%, so the safety
#              behaviour costs about a tenth of what attaching the caveat to every candidate did.
# Env override so a run flips it without editing code: BB_RANKER_CONTRAINDICATIONS=off|relevant|all
# ("1" and "0" are accepted as all/off so the first four frozen runs stay reproducible.)
_CONTRA = {"1": "all", "0": "off"}
RANKER_CONTRAINDICATIONS = _CONTRA.get(
    os.environ.get("BB_RANKER_CONTRAINDICATIONS", "relevant").strip().lower(),
    os.environ.get("BB_RANKER_CONTRAINDICATIONS", "relevant").strip().lower(),
)
if RANKER_CONTRAINDICATIONS not in ("off", "relevant", "all"):
    raise ValueError(f"BB_RANKER_CONTRAINDICATIONS must be off|relevant|all, got {RANKER_CONTRAINDICATIONS!r}")
MAX_DIFFERENTIALS = 6
