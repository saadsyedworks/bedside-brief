from __future__ import annotations

import json

from eval import run_all


def test_smoke_runs_end_to_end_and_resumes(tmp_path):
    run_dir = tmp_path / "smoke"
    assert run_all.main(["--smoke", "--run-dir", str(run_dir)]) == 0
    for name in ("manifest.json", "metrics.json", "metrics.md", "error_analysis.md", "report.md", "figure_bedside_share.svg",
                 "judging_queue.csv", "judging_key.json", "target_map.proposed.json"):
        assert (run_dir / name).exists(), name
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["model"] == "fake-model-smoke" and manifest["cases"]["inputs"] == 9
    assert manifest["counts"] == {a: {"outputs": 9, "errors": 0} for a in "ABC"} and "finished_at" in manifest
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert set(metrics["arms"]) == {"A", "B", "C"}
    assert metrics["arms"]["A"]["bedside_share"]["default"]["share"] == 1.0 and metrics["arms"]["C"]["bedside_share"]["default"]["share"] < 1.0
    assert metrics["arms"]["A"]["evidence_fidelity"]["fidelity"] == 1.0 and metrics["arms"]["C"]["unsupported_claim_rate"]["unsupported"] > 0
    assert metrics["store"]["verified"] == 4 and metrics["store"]["library_coverage"]["mapped_to_verified"] > 0
    report = (run_dir / "report.md").read_text()
    assert "<!-- metrics.json#arms.A.bedside_share.default.share -->" in report and "figure_bedside_share.svg" in report
    svg = (run_dir / "figure_bedside_share.svg").read_text()
    assert svg.startswith("<svg") and "Bedside share" in svg
    # resume: same run dir, nothing recomputed, outputs unchanged
    before = {p.name: p.read_text() for p in (run_dir / "A").glob("*.json")}
    assert run_all.main(["--smoke", "--run-dir", str(run_dir)]) == 0
    assert {p.name: p.read_text() for p in (run_dir / "A").glob("*.json")} == before
