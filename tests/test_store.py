from __future__ import annotations

import copy
import json

import config
from bedside_brief import store
from tests.conftest import EXAM, EXTRACTED, HX, VERIFIED, write_record


def test_loads_all_verified_records(records_dir):
    ids = sorted(r["identity"]["id"] for r in store.load_records())
    assert ids == sorted(r["identity"]["id"] for r in VERIFIED)


def test_schema_invalid_record_rejected(records_dir):
    bad = copy.deepcopy(HX)
    bad["identity"]["id"] = "hx_bad_schema"
    del bad["sources"]  # required by the schema
    write_record(config.RECORDS_VERIFIED, bad)
    assert "hx_bad_schema" not in {r["identity"]["id"] for r in store.load_records()}


def test_vocab_violation_rejected(records_dir):
    bad = copy.deepcopy(HX)
    bad["identity"]["id"] = "hx_bad_vocab"
    bad["clinical_mapping"]["differentials"] = ["aortic_stenosis", "made_up_dx"]
    write_record(config.RECORDS_VERIFIED, bad)
    assert "hx_bad_vocab" not in {r["identity"]["id"] for r in store.load_records()}


def test_bedside_false_and_wrong_tier_rejected(records_dir):
    not_bedside = copy.deepcopy(HX)
    not_bedside["identity"]["id"] = "hx_not_bedside"
    not_bedside["identity"]["bedside"] = False
    write_record(config.RECORDS_VERIFIED, not_bedside)
    smuggled = copy.deepcopy(EXTRACTED)  # tier says extracted but sits in verified/
    write_record(config.RECORDS_VERIFIED, smuggled)
    ids = {r["identity"]["id"] for r in store.load_records()}
    assert "hx_not_bedside" not in ids and "hx_positional_vertigo" not in ids


def test_unreadable_file_skipped_not_raised(records_dir):
    (config.RECORDS_VERIFIED / "hx_broken.json").write_text("{not json")
    assert len(store.load_records()) == len(VERIFIED)


def test_extracted_tier_not_loaded_by_default(records_dir):
    assert all(r["tier"] == "verified" for r in store.load_records())
    ids = {r["identity"]["id"] for r in store.load_records(tiers=("verified", "extracted"))}
    assert "hx_positional_vertigo" in ids


def test_build_index_idempotent_and_queryable(records_dir):
    assert store.build_index() == len(VERIFIED)
    assert store.build_index() == len(VERIFIED)  # drop + recreate, no duplicate rows
    assert store.all_ids() == sorted(r["identity"]["id"] for r in VERIFIED)
    assert store.get_record("hx_exertional_syncope")["identity"]["title"] == "Exertional syncope"
    assert store.get_record("nope") is None
    hits = {r["identity"]["id"] for r in store.records_matching(["aortic_stenosis"])}
    assert hits == {"hx_exertional_syncope", "exam_late_peaking_murmur"}
    assert store.records_matching([]) == []


def test_numbers_in_record_contains_estimate_values():
    nums = store.numbers_in_record(EXAM)
    for expected in ("0.83", "0.75", "0.89", "0.72", "3", "2.2", "4.1", "0.24", "0.66", "4.4", "0.38", "83", "66", "1997"):
        assert expected in nums, expected
    assert "1" not in nums  # record_version / source_index are bookkeeping, not evidence
    assert "2026" not in nums  # timestamps are not evidence
