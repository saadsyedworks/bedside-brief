"""Freeze #1 guard: every benchmark case carries a frozen_commit, and its content (minus the stamp)
is byte-identical to that commit. Any drift fails the suite. Only reference_targets_mapped may change
at freeze #2 (a second commit hash will be recorded in DECISIONS.md)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASES = sorted((ROOT / "benchmark" / "cases").glob("*.json"))
MUTABLE = {"frozen_commit", "reference_targets_mapped"}


def _strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in MUTABLE}


@pytest.mark.parametrize("path", CASES, ids=[p.stem for p in CASES])
def test_case_matches_frozen_commit(path: Path) -> None:
    cur = json.loads(path.read_text())
    h = cur.get("frozen_commit", "")
    assert h, f"{path.name}: frozen_commit is empty — benchmark not frozen"
    rel = path.relative_to(ROOT).as_posix()
    out = subprocess.run(["git", "show", f"{h}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, f"{path.name}: frozen commit {h} not found in git history"
    frozen = json.loads(out.stdout)
    assert _strip(cur) == _strip(frozen), f"{path.name}: content drifted from freeze #1 commit {h}"


def test_all_cases_share_one_freeze_commit() -> None:
    hashes = {json.loads(p.read_text())["frozen_commit"] for p in CASES}
    assert len(hashes) == 1, f"multiple freeze commits: {hashes}"


# Freeze #2 (DECISIONS #26): reference_targets_mapped filled; from here EVERY field is read-only.
FREEZE2_COMMIT = "28a5f2617dcd474602491e71823338316f18bc2d"


@pytest.mark.parametrize("path", CASES, ids=[p.stem for p in CASES])
def test_case_is_byte_identical_to_freeze2(path: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    out = subprocess.run(["git", "show", f"{FREEZE2_COMMIT}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, f"{path.name}: freeze #2 commit {FREEZE2_COMMIT} not found in git history"
    assert json.loads(path.read_text()) == json.loads(out.stdout), f"{path.name}: content drifted from freeze #2 commit {FREEZE2_COMMIT}"
