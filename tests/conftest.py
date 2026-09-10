"""Synthetic record store for the deterministic pipeline tests.

Four VERIFIED records (history, exam with two population estimates, functional
not_quantified, pocus) plus one EXTRACTED packet, all using vocab strings only.
Config paths are monkeypatched at the tmp dir; modules read config at call time.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from bedside_brief import store  # noqa: E402

SOURCE_RCE = {
    "citation": "Etchells E, et al. Does this patient have an abnormal systolic murmur? JAMA.",
    "doi": "10.1001/jama.277.7.564", "pmid": "9039886", "url": None, "kind": "rce_series", "year": 1997,
}
SOURCE_GUIDELINE = {
    "citation": "Shen WK, et al. ACC/AHA/HRS guideline for the evaluation of patients with syncope.",
    "doi": None, "pmid": "28280231", "url": None, "kind": "guideline", "year": 2017,
}


def stat(value: float, lo: float | None = None, hi: float | None = None) -> dict[str, Any]:
    return {"value": value, "ci_low": lo, "ci_high": hi}


def make_record(
    rid: str, rtype: str, presentations: list[str], differentials: list[str], tags: list[str],
    estimates: list[dict[str, Any]], sources: list[dict[str, Any]], evidence_status: str,
    tier: str = "verified", title: str | None = None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "identity": {"id": rid, "title": title or rid.replace("_", " "), "type": rtype, "bedside": True},
        "clinical_mapping": {"presentations": presentations, "syndromes": [], "differentials": differentials, "indication_tags": tags},
        "technique": {"how": f"How to perform {rid}.", "prerequisites": "", "contraindications": ""},
        "interpretation": {
            "positive_finding": f"Positive {rid} finding.", "negative_finding": f"Negative {rid} finding.",
            "pitfalls": "Common pitfall.", "changes_what": "Changes the next action.",
        },
        "estimates": estimates,
        "evidence_status": evidence_status,
        "sources": sources,
        "safety_scope": {"do_not_use_when": "Unstable patient.", "escalation_warning": "", "interobserver_note": ""},
        "tier": tier,
        "extraction_notes": "",
        "agent_id": "extractor-A",
        "extracted_at": "2026-09-10T01:00:00+00:00",
        "verified_by": "owner" if tier == "verified" else None,
        "verified_at": "2026-09-10T02:00:00+00:00" if tier == "verified" else None,
        "verification_notes": "",
        "record_version": 1,
    }
    if rtype == "pocus":
        rec["safety_scope"]["skill_assumption"] = "Basic cardiac POCUS credentialing."
    return rec


def estimate(target: str, population: str, setting: str, **stats: Any) -> dict[str, Any]:
    est = {
        "target_condition": target, "population": population, "setting": setting,
        "reference_standard": "Echocardiography", "prevalence": None, "computed": False,
        "interpretation_label": "rule_in", "evidence_level": "pooled", "source_index": 0,
        "quote": "quote containing the number", "location": "Table 2",
    }
    est.update(stats)
    return est


HX = make_record(
    "hx_exertional_syncope", "history", ["syncope", "chest_pain"], ["aortic_stenosis", "hcm"], ["exertional"],
    [estimate("aortic_stenosis", "adults with syncope", "ED",
              sensitivity=stat(0.85, 0.78, 0.91), specificity=stat(0.60, 0.52, 0.68),
              lr_positive=stat(2.1, 1.5, 3.0), lr_negative=stat(0.25, 0.15, 0.4),
              quote="sensitivity 85% and specificity 60%")],
    [SOURCE_RCE], "quantified", title="Exertional syncope",
)
EXAM = make_record(
    "exam_late_peaking_murmur", "exam", ["syncope", "dyspnea", "chest_pain"], ["aortic_stenosis"], ["elderly"],
    [
        estimate("aortic_stenosis", "outpatients with a systolic murmur", "outpatient",
                 sensitivity=stat(0.83, 0.75, 0.89), specificity=stat(0.72, 0.65, 0.78), lr_positive=stat(3.0, 2.2, 4.1),
                 lr_negative=stat(0.24), quote="late-peaking murmur sensitivity 83%", location="Table 3"),
        estimate("aortic_stenosis", "elderly inpatients", "inpatient",
                 sensitivity=stat(0.66), specificity=stat(0.89), lr_positive=stat(4.4, 3.1, 6.2), lr_negative=stat(0.38),
                 quote="in older inpatients sensitivity 66%", location="Table 4"),
    ],
    [SOURCE_RCE], "quantified", title="Late-peaking systolic murmur",
)
FN = make_record(
    "fn_orthostatic_vitals", "functional", ["syncope", "dizziness"], ["orthostatic_hypotension", "hypovolemic_hemorrhagic_shock"],
    ["orthostatic", "elderly"], [], [SOURCE_GUIDELINE], "not_quantified", title="Orthostatic vital signs",
)
POCUS = make_record(
    "pocus_ivc_collapsibility", "pocus", ["hypotension", "syncope"], ["hypovolemic_hemorrhagic_shock", "pericardial_effusion_tamponade"], [],
    [estimate("hypovolemic_hemorrhagic_shock", "ICU adults", "ICU", sensitivity=stat(0.76, 0.61, 0.86), specificity=stat(0.86, 0.69, 0.95),
              lr_positive=stat(5.3), lr_negative=stat(0.27), quote="IVC collapsibility sensitivity 76%", location="Figure 2")],
    [SOURCE_RCE], "quantified", title="IVC collapsibility",
)
EXTRACTED = make_record(
    "hx_positional_vertigo", "history", ["dizziness"], ["bppv"], ["positional"],
    [estimate("bppv", "ED adults with vertigo", "ED", sensitivity=stat(0.9), specificity=stat(0.5))],
    [SOURCE_RCE], "quantified", tier="extracted", title="Positional vertigo",
)
VERIFIED = [HX, EXAM, FN, POCUS]


def write_record(directory: Path, record: dict[str, Any], suffix: str = "") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record['identity']['id']}{suffix}.json"
    path.write_text(json.dumps(record, indent=1))
    return path


@pytest.fixture
def records_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    verified, extracted = tmp_path / "verified", tmp_path / "extracted"
    for rec in VERIFIED:
        write_record(verified, copy.deepcopy(rec))
    write_record(extracted, copy.deepcopy(EXTRACTED), "__extractor-A")
    monkeypatch.setattr(config, "RECORDS_VERIFIED", verified)
    monkeypatch.setattr(config, "RECORDS_EXTRACTED", extracted)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "index.sqlite")
    return tmp_path


@pytest.fixture
def index_db(records_dir: Path) -> Path:
    store.build_index()
    return config.DB_PATH


@pytest.fixture
def records_by_id(index_db: Path) -> dict[str, dict[str, Any]]:
    return store.load_index(index_db)


@pytest.fixture
def parsed() -> dict[str, Any]:
    return {
        "chief_complaint": "syncope while climbing stairs",
        "presentation": "syncope",
        "time_course": "acute",
        "modifiers": ["exertional"],
        "differentials": [
            {"dx": "aortic_stenosis", "weight": 1.0},
            {"dx": "orthostatic_hypotension", "weight": 0.5},
            {"dx": "hypovolemic_hemorrhagic_shock", "weight": 0.5},
        ],
        "indication_tags": ["exertional"],
        "missing_features": [],
    }
