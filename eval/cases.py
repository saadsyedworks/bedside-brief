"""Benchmark loading: one file per base case -> three CaseInputs (base, _p1, _n1).

DECISIONS #2: 36 files = 108 inputs. Metadata (presentation, targets, should_not_recommend,
off_bedside_acceptable, underspecified flag, expected_change, frozen_commit) is shared by the
three inputs of a file. Freeze protocol (evaluation_rubric.md): refuse to run on a case whose
`frozen_commit` is empty unless `allow_unfrozen=True`.
"""
from __future__ import annotations

import glob
import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import config

log = logging.getLogger("eval.cases")

VARIANT_SUFFIX = {"base": "", "p1": "_p1", "n1": "_n1"}
_FLAG_CLEARS = re.compile(r"underspecified flag should (?:clear|no longer)", re.I)


class FreezeError(RuntimeError):
    """A benchmark file has an empty `frozen_commit` and unfrozen runs were not allowed."""


@dataclass
class Target:
    index: int
    item: str
    rationale: str
    must_have: bool
    mapped_ids: list[str] = field(default_factory=list)  # filled from benchmark/target_map.json by mapping.attach


@dataclass
class CaseInput:
    case_id: str
    base_case_id: str
    variant: str  # base | p1 | n1
    presentation: str
    oneliner: str
    targets: list[Target]
    should_not_recommend: list[str]
    off_bedside_acceptable: list[str]
    underspecified_expected: bool
    expected_change: str  # perturbation/noise text ("" for base)
    changed_feature: str
    expected_change_targets: list[Any]  # optional: target indices (int) or record ids (str) that p1 must surface
    frozen_commit: str
    source_file: str

    @property
    def must_have_targets(self) -> list[Target]:
        return [t for t in self.targets if t.must_have]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _expected_change_targets(case: dict[str, Any], sidecar: dict[str, Any]) -> list[Any]:
    """Optional `expected_change_targets` (case field first, then sidecar file); [] means fallback."""
    pert = case.get("perturbation_pair") or {}
    if pert.get("expected_change_targets"):
        return list(pert["expected_change_targets"])
    return list(sidecar.get(case["case_id"], []) or [])


def expand_case(case: dict[str, Any], source_file: str, sidecar: dict[str, Any] | None = None) -> list[CaseInput]:
    """The three inputs of one benchmark file, base first."""
    sidecar = sidecar or {}
    targets = [
        Target(index=i, item=t["item"], rationale=t.get("rationale", ""), must_have=bool(t.get("must_have")))
        for i, t in enumerate(case["reference_targets_freetext"])
    ]
    base_id = case["case_id"]
    common = dict(
        base_case_id=base_id,
        presentation=case["presentation"],
        should_not_recommend=list(case.get("should_not_recommend") or []),
        off_bedside_acceptable=list(case.get("off_bedside_acceptable") or []),
        frozen_commit=str(case.get("frozen_commit") or ""),
        source_file=source_file,
    )
    under = bool(case.get("underspecified_flag_expected"))
    pert, noise = case["perturbation_pair"], case["noise_variant"]
    # p1 of an underspecified case: the authors say whether the flag should clear (DECISIONS #17).
    under_p1 = False if (under and _FLAG_CLEARS.search(pert.get("expected_change", ""))) else under
    return [
        CaseInput(case_id=base_id, variant="base", oneliner=case["input_oneliner"], targets=[Target(**asdict(t)) for t in targets],
                  underspecified_expected=under, expected_change="", changed_feature="", expected_change_targets=[], **common),
        CaseInput(case_id=pert["case_id"], variant="p1", oneliner=pert["input_oneliner"], targets=[Target(**asdict(t)) for t in targets],
                  underspecified_expected=under_p1, expected_change=pert.get("expected_change", ""),
                  changed_feature=pert.get("changed_feature", ""), expected_change_targets=_expected_change_targets(case, sidecar), **common),
        CaseInput(case_id=noise["case_id"], variant="n1", oneliner=noise["input_oneliner"], targets=[Target(**asdict(t)) for t in targets],
                  underspecified_expected=under, expected_change=noise.get("expected_change", ""),
                  changed_feature=noise.get("changed_feature", ""), expected_change_targets=[], **common),
    ]


def _files(pattern: str | Path | None) -> list[Path]:
    if pattern is None:
        return sorted(Path(config.BENCHMARK_CASES).glob("*.json"))
    p = Path(pattern)
    if p.is_dir():
        return sorted(p.glob("*.json"))
    return sorted(Path(f) for f in glob.glob(str(pattern)))


def load_cases(
    pattern: str | Path | None = None,
    allow_unfrozen: bool = False,
    sidecar_path: str | Path | None = None,
    limit: int | None = None,
) -> list[CaseInput]:
    """Expand every matching benchmark file. Raises FreezeError on an empty frozen_commit."""
    files = _files(pattern)
    if limit is not None:
        files = files[:limit]
    if not files:
        raise FileNotFoundError(f"no benchmark files match {pattern or config.BENCHMARK_CASES}")
    sidecar_path = Path(sidecar_path) if sidecar_path else Path(config.ROOT) / "benchmark" / "expected_change_targets.json"
    sidecar = json.loads(sidecar_path.read_text()) if sidecar_path.exists() else {}
    unfrozen: list[str] = []
    out: list[CaseInput] = []
    for f in files:
        case = json.loads(f.read_text())
        if not str(case.get("frozen_commit") or "").strip():
            unfrozen.append(case.get("case_id", f.name))
        out.extend(expand_case(case, str(f), sidecar))
    if unfrozen:
        if not allow_unfrozen:
            raise FreezeError(
                f"{len(unfrozen)} benchmark file(s) have an empty frozen_commit (e.g. {unfrozen[:3]}); "
                "run the freeze protocol first or pass --allow-unfrozen"
            )
        log.warning("running on %d UNFROZEN case file(s) (--allow-unfrozen): %s", len(unfrozen), ", ".join(unfrozen[:5]))
    return out


def by_base(cases: Iterable[CaseInput]) -> dict[str, dict[str, CaseInput]]:
    """{base_case_id: {"base": ..., "p1": ..., "n1": ...}}"""
    grouped: dict[str, dict[str, CaseInput]] = {}
    for c in cases:
        grouped.setdefault(c.base_case_id, {})[c.variant] = c
    return grouped
