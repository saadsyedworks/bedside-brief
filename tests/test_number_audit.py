"""tools/number_audit.py: placeholder resolution, --fill formatting, UNTRACED / UNRESOLVED / BADCOMMENT /
MISMATCH detection, word counting. Uses a tmp root with a tiny metrics.json, two extracted packets, one
verified record and one benchmark case; never touches the real tree.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from tools import number_audit as na

METRICS = {
    "store": {"verified": 1, "extracted": 2, "not_quantified_share": 1.0, "library_coverage": {"coverage": 0.5}},
    "cases": {"base": 1, "inputs": 3, "perturbation_pairs": 1, "noise_variants": 1},
    "arms": {
        "A": {"bedside_share": {"default": {"share": 0.91234}}, "noise_stability": {"jaccard_mean": 0.4567},
              "n_outputs": 3, "evidence_fidelity": {"fidelity": None}},
        "C": {"bedside_share": {"default": {"share": 0.6}}},
    },
}
MANIFEST = {"model": "gpt-4.1", "frozen_commits": ["39a698e5e79a5b6eddebf090caa3f6c8a1b16f7b"]}
CASE = {
    "case_id": "syncope_001", "presentation": "syncope",
    "reference_targets_freetext": [{"item": "Orthostatic vital signs", "must_have": True}, {"item": "JVP", "must_have": False}],
    "perturbation_pair": {"case_id": "syncope_001_p1"}, "noise_variant": {"case_id": "syncope_001_n1"},
}

ABSTRACT_OK = """# draft
<!-- documentation may quote a `{{namespace:path}}` token; it is not a number -->
## Variant A (comparison)
Bedside share was {{metrics:arms.A.bedside_share.default.share}}<!-- eval/runs/<RUN>/metrics.json#arms.A.bedside_share.default.share -->
versus {{metrics:arms.C.bedside_share.default.share}}<!-- eval/runs/<RUN>/metrics.json#arms.C.bedside_share.default.share -->;
Jaccard {{metrics:arms.A.noise_stability.jaccard_mean}}<!-- eval/runs/<RUN>/metrics.json#arms.A.noise_stability.jaccard_mean -->;
outputs {{metrics:arms.A.n_outputs}}<!-- eval/runs/<RUN>/metrics.json#arms.A.n_outputs -->; model {{manifest:model}}<!-- eval/runs/<RUN>/manifest.json#model -->.
{{store:n_verified}}<!-- records/verified/ (file count) --> of {{store:n_extracted}}<!-- records/extracted/ (distinct ids) --> verified,
{{store:not_quantified_share}}<!-- records/verified/*.json#evidence_status == not_quantified / n_verified --> not quantified across 12 presentations.
Benchmark {{benchmark:n_cases}}<!-- benchmark/cases/*.json (file count) --> cases, {{benchmark:n_inputs}}<!-- benchmark/cases/*.json (base+p1+n1) --> inputs,
{{benchmark:n_must_have}}<!-- benchmark/cases/*.json#reference_targets_freetext[].must_have --> must-have; frozen at 39a698e.
"""


@pytest.fixture
def root(tmp_path: Path) -> Path:
    run = tmp_path / "eval" / "runs" / "dev"
    run.mkdir(parents=True)
    (run / "metrics.json").write_text(json.dumps(METRICS))
    (run / "manifest.json").write_text(json.dumps(MANIFEST))
    ext = tmp_path / "records" / "extracted"
    ext.mkdir(parents=True)
    for name in ("hx_a__extractor-A", "hx_a__extractor-B", "exam_b__extractor-A"):
        (ext / f"{name}.json").write_text("{}")
    ver = tmp_path / "records" / "verified"
    ver.mkdir()
    (ver / "hx_a.json").write_text(json.dumps({"evidence_status": "not_quantified", "clinical_mapping": {"presentations": ["syncope", "dizziness"]}}))
    cases = tmp_path / "benchmark" / "cases"
    cases.mkdir(parents=True)
    (cases / "syncope_001.json").write_text(json.dumps(CASE))
    return tmp_path


def run_audit(root: Path, text: str, fill: bool = False) -> tuple[int, str]:
    abstract = root / "abstract.md"
    abstract.write_text(text)
    out = io.StringIO()
    rc = na.audit(root / "eval" / "runs" / "dev", abstract, fill, root, out)
    return rc, out.getvalue()


def test_store_and_benchmark_counts(root: Path) -> None:
    s = na.store_stats(root / "records")
    assert s == {"n_extracted": 2, "n_verified": 1, "not_quantified": 1, "not_quantified_share": 1.0, "n_presentations_covered": 2}
    b = na.benchmark_stats(root / "benchmark" / "cases")
    assert b == {"n_cases": 1, "n_inputs": 3, "n_perturbation_pairs": 1, "n_noise_variants": 1, "n_targets": 2, "n_must_have": 1, "n_presentations": 1}


def test_resolves_and_fills(root: Path) -> None:
    rc, out = run_audit(root, ABSTRACT_OK, fill=True)
    assert rc == 0, out
    assert "AUDIT OK" in out
    assert "{{metrics:arms.A.bedside_share.default.share}}" in out and "91.2%" in out
    assert "words: Variant A (comparison) =" in out
    filled = (root / "abstract.filled.md").read_text()
    prose = na.COMMENT.sub("", filled)                       # comments are kept in the file; read the prose without them
    assert "{{" not in prose                                 # every placeholder substituted (doc comment may quote one)
    assert "91.2%" in prose and "60.0%" in prose             # shares -> percent, 1 decimal
    assert "Jaccard 0.46" in prose                           # other floats -> 2 decimals
    assert "outputs 3;" in prose and "1 of 2 verified" in prose and "100.0% not quantified" in prose
    assert "Benchmark 1 cases, 3 inputs" in prose and "1 must-have" in prose
    assert "model gpt-4.1" in prose
    assert "<!-- eval/runs/dev/metrics.json#arms.A.bedside_share.default.share -->" in filled  # comments kept, <RUN> filled
    assert "<!-- records/verified/ (file count) -->" in filled


def test_untraced_bare_number_fails(root: Path) -> None:
    rc, out = run_audit(root, ABSTRACT_OK + "\nBedside share rose to 91.2% in 3 cases.\n", fill=True)
    assert rc == 1
    assert "UNTRACED" in out and "'91.2'" in out and "'3'" in out
    assert not (root / "abstract.filled.md").exists()


def test_unresolved_placeholder_fails(root: Path) -> None:
    text = ABSTRACT_OK + "\nfidelity {{metrics:arms.A.evidence_fidelity.fidelity}}<!-- eval/runs/<RUN>/metrics.json#arms.A.evidence_fidelity.fidelity -->" \
                         " judged {{judged:arms.A.relevant_share}}<!-- eval/runs/<RUN>/judged_metrics.json#arms.A.relevant_share -->\n"
    rc, out = run_audit(root, text)
    assert rc == 1
    assert "UNRESOLVED" in out
    assert "{{metrics:arms.A.evidence_fidelity.fidelity}}" in out and "{{judged:arms.A.relevant_share}}" in out
    assert "2 unresolved" in out


def test_bad_or_missing_comment_fails(root: Path) -> None:
    rc, out = run_audit(root, ABSTRACT_OK + "\nalso {{metrics:arms.A.n_outputs}} outputs and {{metrics:arms.C.bedside_share.default.share}}<!-- wrong -->\n")
    assert rc == 1
    assert out.count("BADCOMMENT") == 2


def test_unknown_hash_fails(root: Path) -> None:
    rc, out = run_audit(root, ABSTRACT_OK + "\nfrozen at deadbee1\n")
    assert rc == 1 and "BADHASH" in out


def test_mismatch_with_run_snapshot(root: Path) -> None:
    (root / "records" / "extracted" / "fn_c__extractor-A.json").write_text("{}")  # tree now has 3 ids, run says 2
    rc, out = run_audit(root, ABSTRACT_OK)
    assert rc == 1 and "MISMATCH store:n_extracted: tree says 3" in out


def test_zero_verified_makes_share_unresolved(root: Path) -> None:
    (root / "records" / "verified" / "hx_a.json").unlink()
    m = METRICS | {"store": {**METRICS["store"], "verified": 0}}
    (root / "eval" / "runs" / "dev" / "metrics.json").write_text(json.dumps(m))
    rc, out = run_audit(root, ABSTRACT_OK)
    assert rc == 1 and "UNRESOLVED" in out and "{{store:not_quantified_share}}" in out


def test_word_counts_ignore_comments_and_count_placeholders_once() -> None:
    text = "## Variant B (fallback)\nOne {{store:n_verified}}<!-- a long comment with many words --> two three.\n## Variant A (comparison)\nx y\n"
    assert na.word_counts(text) == {"Variant B (fallback)": 4, "Variant A (comparison)": 2}


def test_overlength_fails(root: Path) -> None:
    rc, out = run_audit(root, ABSTRACT_OK + "\n" + " ".join(["word"] * 400) + "\n")
    assert rc == 1 and "OVERLENGTH" in out


def test_format_value() -> None:
    assert na.format_value("metrics", "arms.A.brevity.pass_rate", 0.0) == "0.0%"
    assert na.format_value("metrics", "store.library_coverage.coverage", 0.83721) == "83.7%"
    assert na.format_value("metrics", "arms.A.items_per_case_mean", 7.126) == "7.13"
    assert na.format_value("benchmark", "n_cases", 36) == "36"
    assert na.format_value("manifest", "model", "gpt-4.1") == "gpt-4.1"
