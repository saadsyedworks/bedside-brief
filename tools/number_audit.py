"""Phase 5 number audit: every number in abstract.md must trace to a harness output file.

    python3 tools/number_audit.py --run-dir eval/runs/<RUN> [--fill] [--abstract abstract.md]

The abstract carries NO literal numbers. Each one is a placeholder `{{namespace:path}}` immediately
followed by an HTML comment naming its source. Namespaces:

  metrics:<json.path>    <run-dir>/metrics.json             (paths as written by eval.metrics)
  manifest:<json.path>   <run-dir>/manifest.json
  judged:<json.path>     <run-dir>/judged_metrics.json      (owner relevance/safety scoring)
  store:n_extracted      distinct ids with >= 1 packet in records/extracted
  store:n_verified       files in records/verified
  store:not_quantified_share   verified records with evidence_status == not_quantified / n_verified
  store:n_presentations_covered  distinct clinical_mapping.presentations across verified records
  benchmark:n_cases | n_inputs | n_perturbation_pairs | n_noise_variants | n_targets | n_must_have
                         counted from benchmark/cases/*.json (DECISIONS #2: one file = base + p1 + n1)

Store and benchmark counts are cross-checked against the run's own `store.*` / `cases.*` block when
present, so a stale run cannot silently disagree with the current tree.

Checks (any failure -> exit 1):
  UNRESOLVED   placeholder has no value (missing file, missing path, null, n_verified == 0 ...)
  UNTRACED     a bare number outside any placeholder / HTML comment / freeze hash / "12 presentations"
  BADCOMMENT   the comment after a placeholder does not name that placeholder's source
  BADHASH      a hex hash that is neither in manifest.frozen_commits nor a commit in this repo
  MISMATCH     store/benchmark count differs from the run's metrics.json snapshot
  OVERLENGTH   a `## Variant` section exceeds the word limit (placeholders count as one word;
               comments do not count)

`--fill` writes abstract.filled.md (shares/rates as percentages with one decimal, other floats with
two decimals, counts as integers, `<RUN>` in comments replaced by the run dir) ONLY when the audit is
clean, so a filled abstract with untraced or missing numbers cannot exist.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORD_LIMIT = 400
PLACEHOLDER = re.compile(r"\{\{\s*([a-z]+)\s*:\s*([^}\s]+)\s*\}\}")
COMMENT = re.compile(r"<!--.*?-->", re.S)
HEX_HASH = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])[0-9a-f]{7,40}\b")
BARE_NUMBER = re.compile(r"\d[\d,.]*")
ALLOWED_LITERALS = ("12 presentations",)
VARIANT_HEADER = re.compile(r"^##\s+Variant\b.*$", re.M)
PCT_SUFFIXES = ("share", "rate", "recall", "coverage", "accuracy", "fidelity")


# --- resolution -------------------------------------------------------------------------------
def get_path(d: Any, path: str) -> Any:
    cur = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def store_stats(records_dir: Path) -> dict[str, Any]:
    extracted = records_dir / "extracted"
    verified = records_dir / "verified"
    ids = {p.name.split("__", 1)[0] for p in extracted.glob("*.json")} if extracted.is_dir() else set()
    vfiles = sorted(verified.glob("*.json")) if verified.is_dir() else []
    nq, pres = 0, set()
    for p in vfiles:
        rec = load_json(p) or {}
        nq += rec.get("evidence_status") == "not_quantified"
        pres.update((rec.get("clinical_mapping") or {}).get("presentations") or [])
    n_ver = len(vfiles)
    return {
        "n_extracted": len(ids),
        "n_verified": n_ver,
        "not_quantified": nq,
        "not_quantified_share": (nq / n_ver) if n_ver else None,
        "n_presentations_covered": len(pres) if n_ver else None,
    }


def benchmark_stats(cases_dir: Path) -> dict[str, Any]:
    files = sorted(cases_dir.glob("*.json")) if cases_dir.is_dir() else []
    n_p1 = n_n1 = n_targets = n_mh = 0
    pres: set[str] = set()
    for p in files:
        c = load_json(p) or {}
        n_p1 += bool(c.get("perturbation_pair"))
        n_n1 += bool(c.get("noise_variant"))
        targets = c.get("reference_targets_freetext") or []
        n_targets += len(targets)
        n_mh += sum(bool(t.get("must_have")) for t in targets)
        if c.get("presentation"):
            pres.add(c["presentation"])
    n = len(files)
    return {
        "n_cases": n or None,
        "n_inputs": (n + n_p1 + n_n1) or None,
        "n_perturbation_pairs": n_p1 if n else None,
        "n_noise_variants": n_n1 if n else None,
        "n_targets": n_targets if n else None,
        "n_must_have": n_mh if n else None,
        "n_presentations": len(pres) if n else None,
    }


@dataclass
class Resolution:
    placeholder: str
    namespace: str
    path: str
    value: Any
    source: str
    ok: bool
    comment: str = ""
    problems: list[str] = field(default_factory=list)


class Resolver:
    def __init__(self, run_dir: Path, root: Path = ROOT) -> None:
        self.run_dir, self.root = run_dir, root
        self.run_label = run_dir.as_posix() if not run_dir.is_absolute() else _relative(run_dir, root)
        self.metrics = load_json(run_dir / "metrics.json")
        self.manifest = load_json(run_dir / "manifest.json")
        self.judged = load_json(run_dir / "judged_metrics.json")
        self.store = store_stats(root / "records")
        self.benchmark = benchmark_stats(root / "benchmark" / "cases")

    def resolve(self, namespace: str, path: str) -> tuple[Any, str]:
        """(value, source path). value None == unresolved."""
        if namespace in ("metrics", "manifest", "judged"):
            data = {"metrics": self.metrics, "manifest": self.manifest, "judged": self.judged}[namespace]
            fname = {"metrics": "metrics.json", "manifest": "manifest.json", "judged": "judged_metrics.json"}[namespace]
            return (None if data is None else get_path(data, path)), f"{self.run_label}/{fname}#{path}"
        if namespace == "store":
            src = {
                "n_extracted": "records/extracted/ (distinct ids)",
                "n_verified": "records/verified/ (file count)",
                "not_quantified_share": "records/verified/*.json#evidence_status == not_quantified / n_verified",
                "n_presentations_covered": "records/verified/*.json#clinical_mapping.presentations (distinct)",
            }
            return self.store.get(path), src.get(path, f"records/ ({path}: unknown statistic)")
        if namespace == "benchmark":
            src = {
                "n_cases": "benchmark/cases/*.json (file count)",
                "n_inputs": "benchmark/cases/*.json (base+p1+n1)",
                "n_perturbation_pairs": "benchmark/cases/*.json#perturbation_pair",
                "n_noise_variants": "benchmark/cases/*.json#noise_variant",
                "n_targets": "benchmark/cases/*.json#reference_targets_freetext",
                "n_must_have": "benchmark/cases/*.json#reference_targets_freetext[].must_have",
                "n_presentations": "benchmark/cases/*.json#presentation (distinct)",
            }
            return self.benchmark.get(path), src.get(path, f"benchmark/cases/ ({path}: unknown statistic)")
        return None, f"(unknown namespace {namespace!r})"

    def cross_checks(self) -> list[str]:
        """Store/benchmark counts vs the run's own snapshot. Returns MISMATCH messages."""
        out: list[str] = []
        if not self.metrics:
            return out
        pairs = [
            ("store.extracted", self.store["n_extracted"], "store:n_extracted"),
            ("store.verified", self.store["n_verified"], "store:n_verified"),
            ("cases.base", self.benchmark["n_cases"], "benchmark:n_cases"),
            ("cases.inputs", self.benchmark["n_inputs"], "benchmark:n_inputs"),
            ("cases.perturbation_pairs", self.benchmark["n_perturbation_pairs"], "benchmark:n_perturbation_pairs"),
            ("cases.noise_variants", self.benchmark["n_noise_variants"], "benchmark:n_noise_variants"),
        ]
        for mpath, tree_value, label in pairs:
            run_value = get_path(self.metrics, mpath)
            if run_value is not None and tree_value is not None and run_value != tree_value:
                out.append(f"MISMATCH {label}: tree says {tree_value}, {self.run_label}/metrics.json#{mpath} says {run_value}")
        return out

    def known_hash(self, h: str) -> str | None:
        """Source of a freeze hash, or None if untraceable."""
        for full in (self.manifest or {}).get("frozen_commits") or []:
            if str(full).startswith(h):
                return f"{self.run_label}/manifest.json#frozen_commits"
        try:
            r = subprocess.run(["git", "-C", str(self.root), "cat-file", "-t", h], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip() == "commit":
                return "git commit (DECISIONS.md freeze hash)"
        except (OSError, subprocess.SubprocessError):
            pass
        return None


def _relative(p: Path, root: Path) -> str:
    try:
        return p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


# --- formatting -------------------------------------------------------------------------------
def format_value(namespace: str, path: str, value: Any) -> str:
    key = path.rsplit(".", 1)[-1]
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if key.endswith(PCT_SUFFIXES) or key == "share":
            return f"{100 * value:.1f}%"
        if float(value).is_integer() and key.startswith("n_"):
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


# --- abstract scanning ------------------------------------------------------------------------
def scan(text: str, resolver: Resolver) -> tuple[list[Resolution], list[str]]:
    """Resolve every placeholder in order; return resolutions and a list of problem lines."""
    resolutions: list[Resolution] = []
    problems: list[str] = []
    comment_spans = [(c.start(), c.end()) for c in COMMENT.finditer(text)]
    for m in PLACEHOLDER.finditer(text):
        if any(a <= m.start() < b for a, b in comment_spans):
            continue  # a placeholder quoted inside an HTML comment (documentation), not a number
        ns, path = m.group(1), m.group(2)
        value, source = resolver.resolve(ns, path)
        res = Resolution(m.group(0), ns, path, value, source, value is not None)
        tail = text[m.end():m.end() + 400]
        cm = re.match(r"\s*(<!--(.*?)-->)", tail, re.S)
        line = text.count("\n", 0, m.start()) + 1
        if cm:
            res.comment = cm.group(2).strip()
            expected = path if ns in ("metrics", "manifest", "judged") else source
            if expected not in res.comment and _short_source(source) not in res.comment:
                res.problems.append(f"BADCOMMENT line {line}: {res.placeholder} comment {res.comment!r} does not name {source}")
        else:
            res.problems.append(f"BADCOMMENT line {line}: {res.placeholder} has no source comment")
        if not res.ok:
            res.problems.append(f"UNRESOLVED line {line}: {res.placeholder} -> {source}")
        problems.extend(res.problems)
        resolutions.append(res)

    # Bare numbers: strip comments, placeholders, allowed literals, then look for digits.
    stripped = COMMENT.sub(" ", text)
    stripped = PLACEHOLDER.sub(" ", stripped)
    for lit in ALLOWED_LITERALS:
        stripped = stripped.replace(lit, " ")
    hashes = {h for h in HEX_HASH.findall(stripped)}
    for h in sorted(hashes):
        src = resolver.known_hash(h)
        if src is None:
            problems.append(f"BADHASH: {h} is not a frozen commit known to the run manifest or this repository")
    stripped = HEX_HASH.sub(" ", stripped)
    for i, line in enumerate(stripped.split("\n"), start=1):
        for n in BARE_NUMBER.findall(line):
            problems.append(f"UNTRACED line {i}: bare number {n!r}")
    return resolutions, problems


def _short_source(source: str) -> str:
    """'records/verified/ (file count)' -> 'records/verified/' ; run-dir sources -> 'metrics.json#path'."""
    if "#" in source and "/" in source.split("#", 1)[0]:
        return source.split("/")[-1]
    return source.split(" (", 1)[0]


def word_counts(text: str) -> dict[str, int]:
    """Words per `## Variant ...` section: comments dropped, each placeholder counts as one word."""
    counts: dict[str, int] = {}
    headers = list(VARIANT_HEADER.finditer(text))
    for i, h in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[h.end():end]
        body = COMMENT.sub(" ", body)
        body = PLACEHOLDER.sub(" N ", body)
        body = re.sub(r"[*#_`]+", " ", body)
        words = [w for w in body.split() if re.search(r"[A-Za-z0-9]", w)]
        counts[h.group(0).strip("# ").split(" —")[0].split(" -")[0].strip()] = len(words)
    return counts


def fill(text: str, resolutions: list[Resolution], run_label: str) -> str:
    values = {r.placeholder: format_value(r.namespace, r.path, r.value) for r in resolutions}
    out = PLACEHOLDER.sub(lambda m: values.get(m.group(0), m.group(0)), text)
    return out.replace("eval/runs/<RUN>", run_label).replace("<RUN>", Path(run_label).name)


# --- CLI ---------------------------------------------------------------------------------------
def audit(run_dir: Path, abstract: Path, do_fill: bool, root: Path = ROOT, out: Any = sys.stdout) -> int:
    text = abstract.read_text()
    resolver = Resolver(run_dir, root)
    if resolver.metrics is None:
        print(f"WARNING: {run_dir / 'metrics.json'} not readable; metrics:* placeholders cannot resolve", file=out)
    resolutions, problems = scan(text, resolver)
    problems.extend(resolver.cross_checks())
    counts = word_counts(text)
    for name, n in counts.items():
        if n > WORD_LIMIT:
            problems.append(f"OVERLENGTH: {name} has {n} words (limit {WORD_LIMIT})")

    w = max([len(r.placeholder) for r in resolutions] + [11])
    print(f"{'placeholder':<{w}} | {'value':>10} | source path", file=out)
    print(f"{'-' * w}-|-{'-' * 10}-|-{'-' * 40}", file=out)
    for r in resolutions:
        val = format_value(r.namespace, r.path, r.value) if r.ok else "UNRESOLVED"
        print(f"{r.placeholder:<{w}} | {val:>10} | {r.source}", file=out)
    print("", file=out)
    for name, n in counts.items():
        print(f"words: {name} = {n} (limit {WORD_LIMIT})", file=out)
    n_ok = sum(r.ok for r in resolutions)
    print(f"placeholders: {len(resolutions)} total, {n_ok} resolved, {len(resolutions) - n_ok} unresolved", file=out)
    if problems:
        print("", file=out)
        for p in problems:
            print(p, file=out)
        print(f"\nAUDIT FAILED: {len(problems)} problem(s)", file=out)
        if do_fill:
            print("abstract.filled.md NOT written (audit must be clean first)", file=out)
        return 1
    print("AUDIT OK: every number traces to a file", file=out)
    if do_fill:
        target = abstract.with_name(abstract.stem + ".filled.md")
        target.write_text(fill(text, resolutions, resolver.run_label))
        print(f"wrote {target}", file=out)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Audit (and optionally fill) the abstract's number placeholders.")
    ap.add_argument("--run-dir", required=True, help="eval/runs/<RUN> holding metrics.json + manifest.json")
    ap.add_argument("--abstract", default=None, help="abstract to audit (default <root>/abstract.md)")
    ap.add_argument("--root", default=None, help="repo root holding records/ and benchmark/ (default: this repo)")
    ap.add_argument("--fill", action="store_true", help="write abstract.filled.md when the audit is clean")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else ROOT
    run_dir = Path(a.run_dir)
    if not run_dir.is_absolute() and not run_dir.exists():
        run_dir = root / run_dir
    abstract = Path(a.abstract) if a.abstract else root / "abstract.md"
    return audit(run_dir, abstract, a.fill, root)


if __name__ == "__main__":
    raise SystemExit(main())
