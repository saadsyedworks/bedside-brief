"""Record store: load + validate records, SQLite index, per-record number inventory.

Only records that pass schema, vocab, tier and bedside checks are ever loaded; a bad
file is logged and skipped, never raised. Paths are read from `config` at call time.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable

import jsonschema

import config
from bedside_brief.validate import normalise_number, scan_numbers

log = logging.getLogger("bedside_brief.store")

try:  # canonical vocab sets live in tools/validate.py
    from tools.validate import DIFFERENTIALS, PRESENTATIONS, TAGS
except Exception:  # pragma: no cover - fallback if tools/ is mid-edit by another agent
    _vocab = json.loads(Path(config.VOCAB_PATH).read_text())
    PRESENTATIONS = set(_vocab["presentations"])
    DIFFERENTIALS = {d for lst in _vocab["presentations"].values() for d in lst}
    TAGS = set(_vocab["indication_tags"])

Record = dict[str, Any]

# Bookkeeping and narrative fields: never rendered, so their digits must not widen the validator
# allow-list. extraction_notes / verification_notes routinely quote numbers that were deliberately
# NOT entered as estimates (ORs, RRs, other cohorts); those are not verified evidence.
_SKIP_KEYS = frozenset({
    "record_version", "source_index", "extracted_at", "verified_at", "agent_id",
    "extraction_notes", "verification_notes",
})

_DDL = """
DROP TABLE IF EXISTS record_tag;
DROP TABLE IF EXISTS record_differential;
DROP TABLE IF EXISTS record_presentation;
DROP TABLE IF EXISTS records;
CREATE TABLE records (
    id TEXT PRIMARY KEY, type TEXT NOT NULL, tier TEXT NOT NULL,
    evidence_status TEXT NOT NULL, json TEXT NOT NULL);
CREATE TABLE record_presentation (id TEXT NOT NULL REFERENCES records(id), presentation TEXT NOT NULL);
CREATE TABLE record_differential (id TEXT NOT NULL REFERENCES records(id), differential TEXT NOT NULL);
CREATE TABLE record_tag (id TEXT NOT NULL REFERENCES records(id), tag TEXT NOT NULL);
CREATE INDEX ix_record_presentation ON record_presentation(presentation);
CREATE INDEX ix_record_differential ON record_differential(differential);
CREATE INDEX ix_record_tag ON record_tag(tag);
CREATE INDEX ix_records_type_tier ON records(type, tier);
"""


def _schema_validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(json.loads(Path(config.SCHEMA_PATH).read_text()))


def record_problems(record: Any, tier: str, validator: jsonschema.Draft202012Validator | None = None) -> list[str]:
    """Reasons a record must not be loaded from the `tier` folder; empty means acceptable."""
    validator = validator or _schema_validator()
    if not isinstance(record, dict):
        return ["not a JSON object"]
    problems = [f"schema {'/'.join(map(str, e.path)) or '<root>'}: {e.message[:100]}" for e in validator.iter_errors(record)]
    if problems:
        return problems
    if record["tier"] != tier:
        problems.append(f"tier is {record['tier']!r} but file lives in {tier}/")
    if record["identity"].get("bedside") is not True:
        problems.append("identity.bedside must be true")
    mapping = record["clinical_mapping"]
    for field_name, allowed in (("presentations", PRESENTATIONS), ("differentials", DIFFERENTIALS), ("indication_tags", TAGS)):
        bad = [x for x in mapping.get(field_name, []) if x not in allowed]
        if bad:
            problems.append(f"{field_name} not in vocab: {bad}")
    return problems


def _tier_files(tier: str) -> list[Path]:
    if tier == "verified":
        return sorted(Path(config.RECORDS_VERIFIED).glob("*.json"))
    if tier == "extracted":
        return sorted(Path(config.RECORDS_EXTRACTED).glob("*__*.json"))
    raise ValueError(f"unknown tier {tier!r}")


def load_records(tiers: Iterable[str] = ("verified",)) -> list[Record]:
    """Load every acceptable record in the given tiers (verified first). Bad files are logged and skipped."""
    validator = _schema_validator()
    records: list[Record] = []
    for tier in sorted(set(tiers), key=lambda t: t != "verified"):
        for path in _tier_files(tier):
            try:
                record = json.loads(path.read_text())
            except (OSError, ValueError) as exc:
                log.warning("skip %s: unreadable (%s)", path.name, exc)
                continue
            problems = record_problems(record, tier, validator)
            if problems:
                log.warning("skip %s: %s", path.name, "; ".join(problems))
                continue
            records.append(record)
    return records


def build_index(db_path: str | Path | None = None, tiers: Iterable[str] = ("verified",)) -> int:
    """(Re)build the SQLite index from disk. One row per id; verified wins over extracted,
    and among duplicate extracted packets the first by filename wins. Returns rows indexed."""
    db_path = Path(db_path or config.DB_PATH)
    by_id: dict[str, Record] = {}
    for record in load_records(tiers):  # verified are loaded first, so they win
        by_id.setdefault(record["identity"]["id"], record)
    with sqlite3.connect(db_path) as con:
        con.executescript(_DDL)
        for rid, record in sorted(by_id.items()):
            identity, mapping = record["identity"], record["clinical_mapping"]
            con.execute(
                "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
                (rid, identity["type"], record["tier"], record["evidence_status"], json.dumps(record, sort_keys=True)),
            )
            con.executemany("INSERT INTO record_presentation VALUES (?, ?)", [(rid, p) for p in mapping["presentations"]])
            con.executemany("INSERT INTO record_differential VALUES (?, ?)", [(rid, d) for d in mapping["differentials"]])
            con.executemany("INSERT INTO record_tag VALUES (?, ?)", [(rid, t) for t in mapping.get("indication_tags", [])])
    log.info("indexed %d records into %s", len(by_id), db_path)
    return len(by_id)


def _connect(db_path: str | Path | None) -> sqlite3.Connection:
    return sqlite3.connect(Path(db_path or config.DB_PATH))


def get_record(record_id: str, db_path: str | Path | None = None) -> Record | None:
    with _connect(db_path) as con:
        row = con.execute("SELECT json FROM records WHERE id = ?", (record_id,)).fetchone()
    return json.loads(row[0]) if row else None


def all_ids(db_path: str | Path | None = None) -> list[str]:
    with _connect(db_path) as con:
        return [r[0] for r in con.execute("SELECT id FROM records ORDER BY id")]


def load_index(db_path: str | Path | None = None) -> dict[str, Record]:
    """Every indexed record keyed by id (the `records_by_id` mapping used by render/validate)."""
    with _connect(db_path) as con:
        return {r[0]: json.loads(r[1]) for r in con.execute("SELECT id, json FROM records ORDER BY id")}


def records_matching(differentials: Iterable[str], db_path: str | Path | None = None) -> list[Record]:
    """Records whose differentials intersect `differentials`, ordered by id."""
    dxs = sorted(set(differentials))
    if not dxs:
        return []
    marks = ",".join("?" * len(dxs))
    with _connect(db_path) as con:
        rows = con.execute(
            f"SELECT DISTINCT r.id, r.json FROM records r JOIN record_differential d ON d.id = r.id "
            f"WHERE d.differential IN ({marks}) ORDER BY r.id",
            dxs,
        ).fetchall()
    return [json.loads(r[1]) for r in rows]


def numbers_in_record(record: Record) -> set[str]:
    """Every numeric literal stored in the record, normalised: numeric fields (values, CI bounds,
    prevalence, year) and digits inside any rendered text field (quote, location, technique,
    citation...). Keys in `_SKIP_KEYS` (bookkeeping + free-text notes) are never counted."""
    found: set[str] = set()

    def walk(node: Any, key: str | None = None) -> None:
        if key in _SKIP_KEYS or isinstance(node, bool) or node is None:
            return
        if isinstance(node, (int, float)):
            found.add(normalise_number(node))
        elif isinstance(node, str):
            found.update(scan_numbers(node))
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, k)
        elif isinstance(node, list):
            for v in node:
                walk(v, key)

    walk(record)
    return found
