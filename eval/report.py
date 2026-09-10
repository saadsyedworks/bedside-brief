"""Report tables + one figure from a run dir. Every number in report.md carries an HTML comment
naming the file and JSON path it came from, so the abstract's number audit can trace it.

Figure: figure_bedside_share.svg (hand-written SVG, no plotting dependency); a PNG is also
written when matplotlib happens to be importable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eval.classify import MODES
from eval.metrics import STRATA, metrics_markdown

ARM_LABELS = {"A": "A Bedside Brief", "B": "B Retrieval-only", "C": "C Generic LLM"}
COLORS = {"A": "#2a6f97", "B": "#8da9c4", "C": "#c9713b"}


def _get(d: dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if cur is None:
            return None
        cur = cur.get(part) if isinstance(cur, dict) else None
    return cur


class Annotated:
    """Formats a metric value with its provenance comment."""

    def __init__(self, metrics: dict[str, Any], src: str) -> None:
        self.m, self.src = metrics, src

    def pct(self, path: str) -> str:
        v = _get(self.m, path)
        return f"{'—' if v is None else f'{100 * v:.1f}%'}<!-- {self.src}#{path} -->"

    def num(self, path: str, digits: int = 2) -> str:
        v = _get(self.m, path)
        s = "—" if v is None else (f"{v:.{digits}f}" if isinstance(v, float) else str(v))
        return f"{s}<!-- {self.src}#{path} -->"


# --- figure ---------------------------------------------------------------------------------
def _bar_panel(x0: float, title: str, series: list[tuple[str, float | None, str]], width: float = 300, height: float = 220) -> str:
    """One panel of vertical bars with value labels. Values are shares in [0,1]."""
    pad_l, pad_b, pad_t = 36, 40, 34
    plot_h = height - pad_b - pad_t
    n = max(len(series), 1)
    slot = (width - pad_l - 10) / n
    bw = slot * 0.6
    parts = [f'<text x="{x0 + width / 2:.0f}" y="18" text-anchor="middle" font-size="13" font-weight="bold">{title}</text>']
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = pad_t + plot_h * (1 - frac)
        parts.append(f'<line x1="{x0 + pad_l}" y1="{y:.1f}" x2="{x0 + width - 10}" y2="{y:.1f}" stroke="#ddd" stroke-width="1"/>')
        parts.append(f'<text x="{x0 + pad_l - 4}" y="{y + 4:.1f}" text-anchor="end" font-size="10" fill="#555">{int(frac * 100)}%</text>')
    for i, (label, value, color) in enumerate(series):
        cx = x0 + pad_l + slot * i + slot / 2
        v = 0.0 if value is None else max(0.0, min(1.0, value))
        h = plot_h * v
        y = pad_t + plot_h - h
        parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{color}"/>')
        txt = "n/a" if value is None else f"{100 * value:.0f}%"
        parts.append(f'<text x="{cx:.1f}" y="{y - 4:.1f}" text-anchor="middle" font-size="11">{txt}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{height - pad_b + 16}" text-anchor="middle" font-size="11">{label}</text>')
    return "\n".join(parts)


def figure_svg(metrics: dict[str, Any]) -> str:
    arms = metrics["arms"]
    share = [(a, _get(arms, f"{a}.bedside_share.default.share"), COLORS[a]) for a in ("A", "C") if a in arms]
    recall = [(a, _get(arms, f"{a}.target_recall_must_have.recall"), COLORS[a]) for a in ("A", "B", "C") if a in arms]
    w, h = 640, 240
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="system-ui, sans-serif">',
            f'<rect width="{w}" height="{h}" fill="#fff"/>',
            _bar_panel(10, "Bedside share (A vs C)", share), _bar_panel(330, "Must-have target recall (A / B / C)", recall),
            f'<text x="{w - 6}" y="{h - 6}" text-anchor="end" font-size="9" fill="#777">source: metrics.json (bedside_share.default.share; target_recall_must_have.recall)</text>',
            "</svg>"]
    return "\n".join(body)


def write_figure(metrics: dict[str, Any], run_dir: Path) -> list[Path]:
    paths = [run_dir / "figure_bedside_share.svg"]
    paths[0].write_text(figure_svg(metrics))
    try:  # optional PNG; the SVG is the deliverable
        import matplotlib  # type: ignore

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore

        arms = metrics["arms"]
        fig, axes = plt.subplots(1, 2, figsize=(8, 3))
        for ax, (title, keys, path) in zip(axes, (("Bedside share (A vs C)", ("A", "C"), "bedside_share.default.share"),
                                                  ("Must-have recall", ("A", "B", "C"), "target_recall_must_have.recall"))):
            ks = [k for k in keys if k in arms]
            ax.bar(ks, [(_get(arms, f"{k}.{path}") or 0.0) for k in ks], color=[COLORS[k] for k in ks])
            ax.set_ylim(0, 1)
            ax.set_title(title)
        fig.tight_layout()
        png = run_dir / "figure_bedside_share.png"
        fig.savefig(png, dpi=150)
        paths.append(png)
    except Exception:  # noqa: BLE001 - matplotlib absent or headless failure: SVG suffices
        pass
    return paths


# --- report ---------------------------------------------------------------------------------
def report_markdown(metrics: dict[str, Any], manifest: dict[str, Any], src: str, judged: dict[str, Any] | None = None) -> str:
    a = Annotated(metrics, src)
    arms = [x for x in ("A", "B", "C") if x in metrics["arms"]]
    L: list[str] = ["# Bedside Brief — evaluation report", ""]
    L.append(f"Run: model `{manifest.get('model')}`, git head `{manifest.get('git_head')}`, frozen commits {manifest.get('frozen_commits')}, "
             f"updated {manifest.get('updated_at')}.<!-- manifest.json -->")
    L.append(f"Provenance: every number below is followed by an HTML comment `<!-- file#json.path -->`; relative files resolve inside "
             f"`{manifest.get('run_dir', '<run dir>')}`.")
    if manifest.get("unfrozen_cases"):
        L.append(f"**WARNING: {len(manifest['unfrozen_cases'])} case file(s) were run UNFROZEN** (empty frozen_commit).<!-- manifest.json#unfrozen_cases -->")
    L += ["", "## Benchmark and store", "",
          f"- Cases: {a.num('cases.base')} base, {a.num('cases.perturbation_pairs')} perturbation pairs, {a.num('cases.noise_variants')} noise variants "
          f"({a.num('cases.inputs')} inputs).",
          f"- Records: {a.num('store.verified')} verified of {a.num('store.extracted')} extracted; not-quantified share {a.pct('store.not_quantified_share')}.",
          f"- Library coverage: {a.pct('store.library_coverage.coverage')} ({a.num('store.library_coverage.mapped_to_verified')} of "
          f"{a.num('store.library_coverage.targets')} targets map to a verified record).",
          "", "## Headline (A vs C)", "", "| Metric | " + " | ".join(ARM_LABELS[x] for x in arms) + " |", "|---|" + "---|" * len(arms)]
    for mode in MODES:
        L.append(f"| Bedside share [{mode}] | " + " | ".join(a.pct(f"arms.{x}.bedside_share.{mode}.share") for x in arms) + " |")
    L.append("| Must-have target recall | " + " | ".join(a.pct(f"arms.{x}.target_recall_must_have.recall") for x in arms) + " |")
    for s in STRATA:
        L.append(f"| &nbsp;&nbsp;must-have recall [{s}] | " + " | ".join(a.pct(f"arms.{x}.target_recall_must_have.strata.{s}.recall") for x in arms) + " |")
    L.append("| Target recall (all) | " + " | ".join(a.pct(f"arms.{x}.target_recall_all.recall") for x in arms) + " |")
    L.append("| Unsupported quantitative claim rate | " + " | ".join(a.pct(f"arms.{x}.unsupported_claim_rate.rate") for x in arms) + " |")
    L.append("| &nbsp;&nbsp;performance numbers only | " + " | ".join(a.pct(f"arms.{x}.unsupported_claim_rate.performance_only.rate") for x in arms) + " |")
    L.append("| Evidence fidelity (A/B) | " + " | ".join(a.pct(f"arms.{x}.evidence_fidelity.fidelity") for x in arms) + " |")
    L.append("| Perturbation responsiveness | " + " | ".join(a.pct(f"arms.{x}.perturbation_responsiveness.rate") for x in arms) + " |")
    L.append("| Noise stability (Jaccard) | " + " | ".join(a.num(f"arms.{x}.noise_stability.jaccard_mean") for x in arms) + " |")
    L.append("| Brevity pass rate | " + " | ".join(a.pct(f"arms.{x}.brevity.pass_rate") for x in arms) + " |")
    L.append("| should_not_recommend case hit rate | " + " | ".join(a.pct(f"arms.{x}.should_not_recommend.case_hit_rate") for x in arms) + " |")
    L.append("| Ask-first correctness | " + " | ".join(a.pct(f"arms.{x}.ask_first.accuracy") for x in arms) + " |")
    L.append("| Errors / outputs | " + " | ".join(f"{a.num(f'arms.{x}.n_errors')} / {a.num(f'arms.{x}.n_outputs')}" for x in arms) + " |")
    if judged and judged.get("arms"):
        j = Annotated(judged, "judged_metrics.json")
        L += ["", "## Judged (single author-reviewer, arm-blinded)", "", "| Metric | " + " | ".join(ARM_LABELS[x] for x in arms if x in judged["arms"]) + " |",
              "|---|" + "---|" * len([x for x in arms if x in judged["arms"]])]
        js = [x for x in arms if x in judged["arms"]]
        L.append("| Relevant share | " + " | ".join(j.pct(f"arms.{x}.relevant_share") for x in js) + " |")
        L.append("| Safety flag rate | " + " | ".join(j.pct(f"arms.{x}.safety_flag_rate") for x in js) + " |")
    if "A" in arms and "B" in arms:
        L += ["", "## Ablation (A vs B: does the LLM ranker earn its place?)", "",
              f"- Must-have recall A {a.pct('arms.A.target_recall_must_have.recall')} vs B {a.pct('arms.B.target_recall_must_have.recall')}.",
              f"- Bedside share A {a.pct('arms.A.bedside_share.default.share')} vs B {a.pct('arms.B.bedside_share.default.share')} (both render store records only).",
              f"- Noise stability A {a.num('arms.A.noise_stability.jaccard_mean')} vs B {a.num('arms.B.noise_stability.jaccard_mean')}."]
    L += ["", "## Figure", "", "![Bedside share A vs C; must-have recall A/B/C](figure_bedside_share.svg)<!-- figure_bedside_share.svg <- metrics.json -->", "",
          "## Full mechanical table", "", f"<!-- generated from {src} by eval.metrics.metrics_markdown -->"]
    L.append(metrics_markdown(metrics).split("\n", 2)[2])  # drop its own H1 + blank
    if metrics.get("notes"):
        L += ["", "## Notes", ""] + [f"- {n}" for n in metrics["notes"]]
    L += ["", "See `error_analysis.md` for the top failure modes of arm A.", ""]
    return "\n".join(L)


def write_report(run_dir: str | Path) -> Path:
    run_dir = Path(run_dir)
    metrics = json.loads((run_dir / "metrics.json").read_text())
    manifest = json.loads((run_dir / "manifest.json").read_text()) if (run_dir / "manifest.json").exists() else {}
    judged_p = run_dir / "judged_metrics.json"
    judged = json.loads(judged_p.read_text()) if judged_p.exists() else None
    write_figure(metrics, run_dir)
    p = run_dir / "report.md"
    manifest.setdefault("run_dir", str(run_dir))
    p.write_text(report_markdown(metrics, manifest, "metrics.json", judged))
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    a = ap.parse_args(argv)
    print(write_report(a.run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
