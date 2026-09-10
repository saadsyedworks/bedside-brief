"""Deterministic validators for Phase 0 artifacts.

  python tools/validate.py ids   [path]      # discriminator_ids.json against vocab + naming rules
  python tools/validate.py cases [dir]       # benchmark/cases/*.json against template + vocab
  python tools/validate.py records [dir]     # records/**.json against discriminator_schema.json + vocab
Exit code 1 on any error. Warnings do not fail.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB = json.loads((ROOT / "vocab.json").read_text())
PRESENTATIONS = set(VOCAB["presentations"])
DIFFERENTIALS = {d for lst in VOCAB["presentations"].values() for d in lst}
TAGS = set(VOCAB["indication_tags"])
ID_RE = re.compile(r"^(hx|exam|fn|pocus)_[a-z0-9_]+$")
TYPE_PREFIX = {"history": "hx", "exam": "exam", "functional": "fn", "pocus": "pocus"}
EVIDENCE = {"rce_backed", "likely_quantified", "likely_not_quantified"}
TEMPLATE_KEYS = [
    k for k in json.loads((ROOT / "benchmark_case_template.json").read_text()) if not k.startswith("_")
]


def validate_ids(path: Path) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    data = json.loads(path.read_text())
    ids = data["ids"]
    seen = set()
    for e in ids:
        i = e.get("id", "?")
        if not ID_RE.match(i):
            errs.append(f"{i}: bad id pattern")
        if i in seen:
            errs.append(f"{i}: duplicate id")
        seen.add(i)
        if e.get("type") not in TYPE_PREFIX:
            errs.append(f"{i}: bad type {e.get('type')}")
        elif not i.startswith(TYPE_PREFIX[e["type"]] + "_"):
            errs.append(f"{i}: prefix does not match type {e['type']}")
        for p in e.get("presentations", []):
            if p not in PRESENTATIONS:
                errs.append(f"{i}: presentation not in vocab: {p}")
        if not e.get("presentations"):
            errs.append(f"{i}: no presentations")
        for d in e.get("differentials", []):
            if d not in DIFFERENTIALS:
                errs.append(f"{i}: differential not in vocab: {d}")
        if not e.get("differentials"):
            errs.append(f"{i}: no differentials")
        for t in e.get("indication_tags", []):
            if t not in TAGS:
                errs.append(f"{i}: tag not in vocab: {t}")
        if e.get("expected_evidence") not in EVIDENCE:
            errs.append(f"{i}: bad expected_evidence")
        if e.get("priority") not in (1, 2, 3):
            errs.append(f"{i}: priority must be 1/2/3")
        if not e.get("title"):
            errs.append(f"{i}: missing title")
        if e.get("expected_evidence") == "rce_backed" and not e.get("anchor_source"):
            warns.append(f"{i}: rce_backed without anchor_source")
    return errs, warns


def _words(s: str) -> int:
    return len(s.split())


def validate_cases(d: Path) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    files = sorted(d.glob("*.json"))
    under = []
    per_pres: dict[str, int] = {}
    for f in files:
        try:
            c = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            errs.append(f"{f.name}: invalid JSON ({e})")
            continue
        missing = [k for k in TEMPLATE_KEYS if k not in c]
        extra = [k for k in c if k not in TEMPLATE_KEYS]
        if missing:
            errs.append(f"{f.name}: missing keys {missing}")
        if extra:
            errs.append(f"{f.name}: extra keys {extra}")
        cid = c.get("case_id", "")
        if f.stem != cid:
            errs.append(f"{f.name}: case_id {cid} != filename")
        pres = c.get("presentation")
        if pres not in PRESENTATIONS:
            errs.append(f"{f.name}: presentation not in vocab: {pres}")
        else:
            per_pres[pres] = per_pres.get(pres, 0) + 1
            if not cid.startswith(pres + "_"):
                errs.append(f"{f.name}: case_id does not start with presentation")
        for dx in c.get("intended_bedside_differential", []):
            if dx not in DIFFERENTIALS:
                errs.append(f"{f.name}: differential not in vocab: {dx}")
        n = len(c.get("intended_bedside_differential", []))
        if not 2 <= n <= 4:
            warns.append(f"{f.name}: {n} differentials (want 2-4)")
        tg = c.get("reference_targets_freetext", [])
        if not 3 <= len(tg) <= 8:
            errs.append(f"{f.name}: {len(tg)} targets (want 3-8; >6 only after compound splits)")
        mh = sum(1 for t in tg if t.get("must_have"))
        if mh < 2:
            errs.append(f"{f.name}: only {mh} must_have targets")
        for t in tg:
            for k in ("item", "rationale", "must_have"):
                if k not in t:
                    errs.append(f"{f.name}: target missing {k}")
        w = _words(c.get("input_oneliner", ""))
        if not 12 <= w <= 30:
            warns.append(f"{f.name}: one-liner {w} words")
        if c.get("reference_targets_mapped") != []:
            errs.append(f"{f.name}: reference_targets_mapped must be [] before freeze #2")
        if c.get("underspecified_flag_expected"):
            under.append(cid)
        for key, suf in (("perturbation_pair", "_p1"), ("noise_variant", "_n1")):
            v = c.get(key, {})
            if v.get("case_id") != cid + suf:
                errs.append(f"{f.name}: {key}.case_id should be {cid + suf}")
            for k in ("changed_feature", "input_oneliner", "expected_change"):
                if not v.get(k):
                    errs.append(f"{f.name}: {key}.{k} empty")
            if v.get("input_oneliner") == c.get("input_oneliner"):
                errs.append(f"{f.name}: {key} one-liner identical to base")
        if not str(c.get("noise_variant", {}).get("expected_change", "")).startswith("None"):
            errs.append(f"{f.name}: noise_variant.expected_change must start with 'None'")
        if not c.get("should_not_recommend"):
            warns.append(f"{f.name}: no should_not_recommend items")
    for p in PRESENTATIONS:
        if per_pres.get(p, 0) != 3:
            warns.append(f"{p}: {per_pres.get(p, 0)} base cases (want 3)")
    if files and not 2 <= len(under) <= 4:
        warns.append(f"underspecified cases: {len(under)} {under} (want ~3)")
    return errs, warns


def validate_records(d: Path) -> tuple[list[str], list[str]]:
    import jsonschema  # local import so ids/cases validation needs no deps

    schema = json.loads((ROOT / "discriminator_schema.json").read_text())
    v = jsonschema.Draft202012Validator(schema)
    errs, warns = [], []
    for f in sorted(d.rglob("*.json")):
        try:
            r = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            errs.append(f"{f.name}: invalid JSON ({e})")
            continue
        for e in v.iter_errors(r):
            errs.append(f"{f.name}: {'/'.join(map(str, e.path))}: {e.message[:120]}")
        cm = r.get("clinical_mapping", {})
        for p in cm.get("presentations", []):
            if p not in PRESENTATIONS:
                errs.append(f"{f.name}: presentation not in vocab: {p}")
        for dx in cm.get("differentials", []):
            if dx not in DIFFERENTIALS:
                errs.append(f"{f.name}: differential not in vocab: {dx}")
        for t in cm.get("indication_tags", []):
            if t not in TAGS:
                errs.append(f"{f.name}: tag not in vocab: {t}")
        rid = r.get("identity", {}).get("id", "")
        if rid and not f.name.startswith(rid):
            errs.append(f"{f.name}: filename does not start with identity.id {rid}")
        for i, est in enumerate(r.get("estimates", [])):
            has_num = any(est.get(k) for k in ("sensitivity", "specificity", "lr_positive", "lr_negative"))
            if has_num and (not est.get("quote") or not est.get("location")):
                errs.append(f"{f.name}: estimates[{i}] numeric without quote+location")
            if est.get("quote") and len(est["quote"].split()) > 25:
                warns.append(f"{f.name}: estimates[{i}] quote > 25 words")
            if est.get("computed") and not est.get("computed_from"):
                errs.append(f"{f.name}: estimates[{i}] computed without computed_from")
            for fld in ("sensitivity", "specificity"):
                st = est.get(fld)
                if isinstance(st, dict) and isinstance(st.get("value"), (int, float)) and st["value"] > 1:
                    errs.append(f"{f.name}: estimates[{i}].{fld} must be a proportion 0-1 (got {st['value']}); run tools/normalize_units.py")
            si = est.get("source_index")
            if si is None or si >= len(r.get("sources", [])):
                errs.append(f"{f.name}: estimates[{i}] bad source_index")
        for j, s in enumerate(r.get("sources", [])):
            if not (s.get("doi") or s.get("pmid")):
                warns.append(f"{f.name}: sources[{j}] has neither DOI nor PMID")
    return errs, warns


def main() -> int:
    what = sys.argv[1] if len(sys.argv) > 1 else "cases"
    arg = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if what == "ids":
        errs, warns = validate_ids(arg or ROOT / "discriminator_ids.json")
    elif what == "cases":
        errs, warns = validate_cases(arg or ROOT / "benchmark" / "cases")
    elif what == "records":
        errs, warns = validate_records(arg or ROOT / "records")
    else:
        print(__doc__)
        return 2
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    print(f"{what}: {len(errs)} errors, {len(warns)} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
