"""Owner verification UI: two extraction packets side by side, one-click promote / reject / edit-later.

  python3 tools/verify_ui.py [--port 8765] [--records-dir records] [--only id,id] [--open]

Queue (/) follows tools/diff_report.py's suggested verification order: fabrication suspects and
disagreements first, then rce_backed agreements, then the rest. Record page (/r/{id}) shows packet A,
packet B and an editable "verified draft" (pre-filled from A, or B via ?from=B, or a saved draft).

Only the owner promotes (CLAUDE.md gate 2). Promote validates the draft against
discriminator_schema.json + vocab.json (via bedside_brief.store.record_problems and the extra
record-level rules of tools/validate.py) and writes records/verified/{id}.json with tier=verified,
verified_by=owner, verified_at=now. Nothing is ever written outside records/{verified,rejected,drafts}/.
No LLM calls. No secrets are read or printed.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bedside_brief.store import record_problems  # noqa: E402  (schema + vocab + tier + bedside)
from tools.diff_report import STATS, _est_key, compare  # noqa: E402
from tools.validate import validate_records  # noqa: E402

TEMPLATES = ROOT / "tools" / "templates" / "verify"
VERIFIED_BY = "owner"
LIST_FIELDS = ("presentations", "syndromes", "differentials", "indication_tags")
TECHNIQUE_FIELDS = ("how", "prerequisites", "contraindications")
INTERPRETATION_FIELDS = ("positive_finding", "negative_finding", "pitfalls", "changes_what")
SAFETY_FIELDS = ("do_not_use_when", "skill_assumption", "escalation_warning", "interobserver_note")
EVIDENCE_STATUS = ("quantified", "partially_quantified", "not_quantified")
RECORD_TYPES = ("history", "exam", "functional", "pocus")
ESTIMATE_REQUIRED = ("target_condition", "population", "setting", "reference_standard", "source_index")
_ID_RE = re.compile(r"^[a-z]+_[a-z0-9_]+$")
_PMID_RE = re.compile(r"^\d{1,9}$")
_DOI_RE = re.compile(r"^10\.\S+$")


# ----------------------------------------------------------------------------- loading


def load_packets(extracted_dir: Path) -> dict[str, dict[str, dict]]:
    """Same shape as tools.diff_report.load_packets, but for an explicit directory."""
    out: dict[str, dict[str, dict]] = defaultdict(dict)
    for f in sorted(extracted_dir.glob("*__*.json")):
        rid, agent = f.stem.split("__", 1)
        try:
            out[rid][agent] = json.loads(f.read_text())
        except Exception as e:  # noqa: BLE001
            out[rid][agent] = {"_invalid": str(e)}
    return dict(out)


def load_ids_meta(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    try:
        return {e["id"]: e for e in json.loads(path.read_text()).get("ids", [])}
    except Exception:  # noqa: BLE001
        return {}


def redteam_mentions(redteam_dir: Path, rid: str) -> list[dict[str, str]]:
    """Lines of records/redteam/*.md that mention the id (plain substring grep)."""
    hits: list[dict[str, str]] = []
    if not redteam_dir.is_dir():
        return hits
    for f in sorted(redteam_dir.glob("*.md")):
        try:
            for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                if rid in line:
                    hits.append({"file": f.name, "line": n, "text": line.strip()})
        except OSError:
            continue
    return hits


def source_url(src: dict | None) -> str | None:
    """Deterministic link: PubMed by PMID, else doi.org by DOI, else nothing."""
    if not isinstance(src, dict):
        return None
    pmid = str(src.get("pmid") or "").strip()
    if _PMID_RE.match(pmid):
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    doi = str(src.get("doi") or "").strip()
    if _DOI_RE.match(doi):
        return "https://doi.org/" + quote(doi, safe="/()._-:;")
    return None


# ----------------------------------------------------------------------------- queue


def order_key(row: dict, ids_meta: dict[str, dict]) -> tuple:
    """Verbatim from tools/diff_report.py main(): hard flags, then disagree, then rce_backed, then id."""
    hard = any(f.startswith(("FABRICATION", "NUMERIC MISMATCH", "INVALID", "STATUS MISMATCH")) for f in row["flags"])
    rce = ids_meta.get(row["id"], {}).get("expected_evidence") == "rce_backed"
    return (0 if hard else 1, 0 if row["status"] == "disagree" else 1, 0 if rce else 1, row["id"])


class VerifyState:
    def __init__(self, records_dir: Path, only: list[str] | None = None, ids_path: Path | None = None) -> None:
        self.records_dir = Path(records_dir)
        self.only = [x for x in (only or []) if x]
        self.ids_meta = load_ids_meta(ids_path or ROOT / "discriminator_ids.json")

    @property
    def extracted(self) -> Path:
        return self.records_dir / "extracted"

    @property
    def verified(self) -> Path:
        return self.records_dir / "verified"

    @property
    def rejected(self) -> Path:
        return self.records_dir / "rejected"

    @property
    def drafts(self) -> Path:
        return self.records_dir / "drafts"

    @property
    def redteam(self) -> Path:
        return self.records_dir / "redteam"

    def packets(self) -> dict[str, dict[str, dict]]:
        packs = load_packets(self.extracted)
        if self.only:
            packs = {k: v for k, v in packs.items() if k in self.only}
        return packs

    def queue(self) -> list[dict]:
        rows = [compare(rid, packs, resolve=False) for rid, packs in self.packets().items()]
        rows.sort(key=lambda r: order_key(r, self.ids_meta))
        for r in rows:
            first = next((p for p in self.packets_for(r["id"]).values() if "_invalid" not in p), {})
            r["title"] = first.get("identity", {}).get("title", "")
            r["type"] = first.get("identity", {}).get("type", "")
            r["expected_evidence"] = self.ids_meta.get(r["id"], {}).get("expected_evidence", "")
            r["verified"] = (self.verified / f"{r['id']}.json").exists()
            r["rejected"] = (self.rejected / f"{r['id']}.json").exists()
            r["draft"] = (self.drafts / f"{r['id']}.json").exists()
            r["redteam"] = redteam_mentions(self.redteam, r["id"])
        return rows

    def packets_for(self, rid: str) -> dict[str, dict]:
        return self.packets().get(rid, {})

    def next_id(self, rid: str) -> str | None:
        """Next id after `rid` in queue order that is neither verified nor rejected."""
        ids = [r["id"] for r in self.queue() if not (r["verified"] or r["rejected"])]
        order = [r["id"] for r in self.queue()]
        if rid not in order:
            return ids[0] if ids else None
        pos = order.index(rid)
        return next((i for i in order[pos + 1:] if i in ids), None)

    def existing_verified(self, rid: str) -> dict | None:
        p = self.verified / f"{rid}.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            return None

    def existing_draft(self, rid: str) -> dict | None:
        p = self.drafts / f"{rid}.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except Exception:  # noqa: BLE001
            return None


# ----------------------------------------------------------------------------- diff view


def _norm(v: Any) -> Any:
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return sorted(x.strip() for x in v)
    return v


def _row(section: str, field: str, a: Any, b: Any, link_a: str | None = None, link_b: str | None = None) -> dict:
    return {"section": section, "field": field, "a": a, "b": b, "diff": _norm(a) != _norm(b), "link_a": link_a, "link_b": link_b}


def _fmt(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _stat(e: dict, k: str) -> str:
    v = e.get(k)
    if not isinstance(v, dict) or v.get("value") is None:
        return ""
    s = str(v["value"])
    if v.get("ci_low") is not None or v.get("ci_high") is not None:
        s += f" ({v.get('ci_low')}–{v.get('ci_high')})"
    return s


def _estimate_view(e: dict, sources: list[dict]) -> dict:
    si = e.get("source_index")
    src = sources[si] if isinstance(si, int) and 0 <= si < len(sources) else None
    return {
        "key": _est_key(e),
        "fields": [
            ("target_condition", _fmt(e.get("target_condition"))),
            ("population", _fmt(e.get("population"))),
            ("setting", _fmt(e.get("setting"))),
            ("reference_standard", _fmt(e.get("reference_standard"))),
            ("prevalence", _fmt(e.get("prevalence"))),
            ("sensitivity", _stat(e, "sensitivity")),
            ("specificity", _stat(e, "specificity")),
            ("lr_positive", _stat(e, "lr_positive")),
            ("lr_negative", _stat(e, "lr_negative")),
            ("computed", _fmt(e.get("computed"))),
            ("computed_from", _fmt(e.get("computed_from"))),
            ("interpretation_label", _fmt(e.get("interpretation_label"))),
            ("evidence_level", _fmt(e.get("evidence_level"))),
            ("quote", _fmt(e.get("quote"))),
            ("location", _fmt(e.get("location"))),
        ],
        "source_index": si,
        "citation": (src or {}).get("citation", "") if src else "(bad source_index)",
        "url": source_url(src),
    }


def field_diff(a: dict, b: dict) -> list[dict]:
    """Field-by-field comparison rows for the scalar/list sections (estimates and sources handled apart)."""
    rows: list[dict] = []
    for f in ("id", "title", "type"):
        rows.append(_row("identity", f, _fmt(a.get("identity", {}).get(f)), _fmt(b.get("identity", {}).get(f))))
    for f in LIST_FIELDS:
        rows.append(_row("clinical_mapping", f, a.get("clinical_mapping", {}).get(f, []), b.get("clinical_mapping", {}).get(f, [])))
    for f in TECHNIQUE_FIELDS:
        rows.append(_row("technique", f, _fmt(a.get("technique", {}).get(f)), _fmt(b.get("technique", {}).get(f))))
    for f in INTERPRETATION_FIELDS:
        rows.append(_row("interpretation", f, _fmt(a.get("interpretation", {}).get(f)), _fmt(b.get("interpretation", {}).get(f))))
    rows.append(_row("evidence", "evidence_status", _fmt(a.get("evidence_status")), _fmt(b.get("evidence_status"))))
    for f in SAFETY_FIELDS:
        rows.append(_row("safety_scope", f, _fmt(a.get("safety_scope", {}).get(f)), _fmt(b.get("safety_scope", {}).get(f))))
    rows.append(_row("notes", "extraction_notes", _fmt(a.get("extraction_notes")), _fmt(b.get("extraction_notes"))))
    for r in rows:
        r["a"], r["b"] = _fmt(r["a"]), _fmt(r["b"])
    return rows


def estimate_pairs(a: dict, b: dict) -> list[dict]:
    """Align estimates by diff_report's key; each pair carries per-stat diff flags."""
    sa, sb = a.get("sources", []) or [], b.get("sources", []) or []
    ea = [(_est_key(e), e) for e in a.get("estimates", []) or []]
    eb = {_est_key(e): e for e in b.get("estimates", []) or []}
    used: set[str] = set()
    pairs: list[dict] = []
    for k, e in ea:
        m = eb.get(k) if k not in used else None
        if m is not None:
            used.add(k)
        pairs.append(_pair(e, m, sa, sb))
    for k, e in eb.items():
        if k not in used:
            pairs.append(_pair(None, e, sa, sb))
    return pairs


def _pair(ea: dict | None, eb: dict | None, sa: list, sb: list) -> dict:
    va = _estimate_view(ea, sa) if ea is not None else None
    vb = _estimate_view(eb, sb) if eb is not None else None
    diffs: set[str] = set()
    if va and vb:
        for (fa, xa), (fb, xb) in zip(va["fields"], vb["fields"]):
            if _norm(xa) != _norm(xb):
                diffs.add(fa)
    else:
        diffs.add("*")
    return {"a": va, "b": vb, "diffs": diffs, "missing": va is None or vb is None}


def sources_view(p: dict) -> list[dict]:
    out = []
    for i, s in enumerate(p.get("sources", []) or []):
        out.append({"index": i, "citation": _fmt(s.get("citation")), "kind": _fmt(s.get("kind")), "year": _fmt(s.get("year")),
                    "pmid": _fmt(s.get("pmid")), "doi": _fmt(s.get("doi")), "url": source_url(s)})
    return out


# ----------------------------------------------------------------------------- draft <-> form


def _split_list(s: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,\n]", s or "") if x.strip()]


def draft_form_values(rec: dict) -> dict[str, Any]:
    """Flatten a record into the form's field values."""
    ident, cm, tech, interp, safe = (rec.get(k, {}) or {} for k in ("identity", "clinical_mapping", "technique", "interpretation", "safety_scope"))
    v: dict[str, Any] = {"id": ident.get("id", ""), "title": ident.get("title", ""), "type": ident.get("type", "exam")}
    for f in LIST_FIELDS:
        v[f] = ", ".join(cm.get(f, []) or [])
    for f in TECHNIQUE_FIELDS:
        v[f] = tech.get(f, "") or ""
    for f in INTERPRETATION_FIELDS:
        v[f] = interp.get(f, "") or ""
    for f in SAFETY_FIELDS:
        v[f] = safe.get(f, "") or ""
    v["evidence_status"] = rec.get("evidence_status", "not_quantified")
    v["estimates_json"] = json.dumps(rec.get("estimates", []), indent=1, ensure_ascii=False)
    v["sources_json"] = json.dumps(rec.get("sources", []), indent=1, ensure_ascii=False)
    v["extraction_notes"] = rec.get("extraction_notes", "") or ""
    v["verification_notes"] = rec.get("verification_notes", "") or ""
    v["base_agent"] = rec.get("agent_id", "") or ""
    v["extracted_at"] = rec.get("extracted_at", "") or ""
    return v


def _parse_json_list(text: str, name: str, problems: list[str]) -> list:
    try:
        val = json.loads(text or "[]")
    except ValueError as e:
        problems.append(f"{name}: not valid JSON ({e})")
        return []
    if not isinstance(val, list):
        problems.append(f"{name}: must be a JSON array")
        return []
    return val


def form_to_draft(rid: str, form: dict[str, str]) -> tuple[dict, list[str]]:
    """Rebuild a record dict from submitted form fields. Returns (record, hard problems)."""
    problems: list[str] = []
    g = lambda k: (form.get(k) or "").strip()  # noqa: E731
    rec: dict[str, Any] = {
        "identity": {"id": rid, "title": g("title"), "type": g("type"), "bedside": True},
        "clinical_mapping": {f: _split_list(form.get(f, "")) for f in LIST_FIELDS},
        "technique": {f: g(f) for f in TECHNIQUE_FIELDS},
        "interpretation": {f: g(f) for f in INTERPRETATION_FIELDS},
        "estimates": _parse_json_list(form.get("estimates_json", "[]"), "estimates", problems),
        "evidence_status": g("evidence_status"),
        "sources": _parse_json_list(form.get("sources_json", "[]"), "sources", problems),
        "safety_scope": {f: g(f) for f in SAFETY_FIELDS if g(f) or f != "skill_assumption"},
        "tier": "extracted",
        "extraction_notes": g("extraction_notes"),
        "agent_id": g("base_agent") or "owner-draft",
        "extracted_at": g("extracted_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verified_by": None,
        "verified_at": None,
        "verification_notes": g("verification_notes"),
        "record_version": 1,
    }
    for i, e in enumerate(rec["estimates"]):
        if not isinstance(e, dict):
            problems.append(f"estimates[{i}]: must be an object")
            continue
        for k in ESTIMATE_REQUIRED:
            if k not in e:
                problems.append(f"estimates[{i}]: missing {k}")
    for j, s in enumerate(rec["sources"]):
        if not isinstance(s, dict):
            problems.append(f"sources[{j}]: must be an object")
    return rec, problems


def extra_record_checks(rec: dict) -> list[str]:
    """The record-level rules tools/validate.py enforces beyond the schema (quote+location, computed_from, units, source_index)."""
    errs: list[str] = []
    for i, est in enumerate(rec.get("estimates", [])):
        if not isinstance(est, dict):
            continue
        has_num = any(est.get(k) for k in STATS)
        if has_num and (not est.get("quote") or not est.get("location")):
            errs.append(f"estimates[{i}]: numeric without quote+location")
        if est.get("computed") and not est.get("computed_from"):
            errs.append(f"estimates[{i}]: computed without computed_from")
        for fld in ("sensitivity", "specificity"):
            st = est.get(fld)
            if isinstance(st, dict) and isinstance(st.get("value"), (int, float)) and st["value"] > 1:
                errs.append(f"estimates[{i}].{fld}: must be a proportion 0-1 (got {st['value']})")
        si = est.get("source_index")
        if not isinstance(si, int) or si < 0 or si >= len(rec.get("sources", [])):
            errs.append(f"estimates[{i}]: bad source_index")
    return errs


def promote_record(state: VerifyState, rid: str, draft: dict) -> tuple[dict | None, list[str]]:
    """Stamp verified fields, validate, write records/verified/{id}.json. Returns (record, problems)."""
    rec = copy.deepcopy(draft)
    prev = state.existing_verified(rid)
    rec["tier"] = "verified"
    rec["verified_by"] = VERIFIED_BY
    rec["verified_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rec["record_version"] = int((prev or {}).get("record_version", 0) or 0) + 1
    if rec["identity"].get("id") != rid or not _ID_RE.match(rid):
        return None, [f"identity.id must be {rid}"]
    problems = record_problems(rec, "verified") + extra_record_checks(rec)
    if problems:
        return None, problems
    state.verified.mkdir(parents=True, exist_ok=True)
    target = state.verified / f"{rid}.json"
    prev_text = target.read_text() if target.exists() else None
    target.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    # Belt and braces: run the repo validator over the saved file; roll back if it objects.
    errs, _ = validate_records(state.verified)
    mine = [e for e in errs if e.startswith(target.name + ":")]
    if mine:
        if prev_text is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(prev_text)
        return None, ["saved file failed tools/validate.py: " + "; ".join(mine)]
    return rec, []


# ----------------------------------------------------------------------------- app


def create_app(records_dir: Path, only: list[str] | None = None, ids_path: Path | None = None) -> FastAPI:
    state = VerifyState(records_dir, only, ids_path)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=select_autoescape(["html"]))
    app = FastAPI(title="Bedside Brief — verification queue")
    app.state.verify = state

    def render(name: str, status_code: int = 200, **ctx: Any) -> HTMLResponse:
        return HTMLResponse(env.get_template(name).render(**ctx), status_code=status_code)

    def _after(rid: str) -> RedirectResponse:
        nxt = state.next_id(rid)
        return RedirectResponse(f"/r/{nxt}" if nxt else "/", status_code=303)

    def _record_ctx(rid: str, draft: dict, form_values: dict, problems: list[str], from_agent: str, notice: str = "") -> dict:
        packs = state.packets_for(rid)
        if not packs:
            raise HTTPException(404, f"no extracted packets for {rid}")
        agents = sorted(packs)
        pa = packs[agents[0]]
        pb = packs[agents[1]] if len(agents) > 1 else {}
        invalid = {a: p["_invalid"] for a, p in packs.items() if "_invalid" in p}
        pa = {} if "_invalid" in pa else pa
        pb = {} if "_invalid" in pb else pb
        cmp = compare(rid, packs, resolve=False)
        return {
            "rid": rid, "agents": agents, "agent_a": agents[0], "agent_b": agents[1] if len(agents) > 1 else "(none)",
            "invalid": invalid, "cmp": cmp, "rows": field_diff(pa, pb), "estimates": estimate_pairs(pa, pb),
            "sources_a": sources_view(pa), "sources_b": sources_view(pb),
            "form": form_values, "problems": problems, "from_agent": from_agent, "notice": notice,
            "existing": state.existing_verified(rid), "has_draft": state.existing_draft(rid) is not None,
            "redteam": redteam_mentions(state.redteam, rid), "next_id": state.next_id(rid),
            "evidence_status_options": EVIDENCE_STATUS, "type_options": RECORD_TYPES,
        }

    @app.get("/", response_class=HTMLResponse)
    def queue() -> HTMLResponse:
        rows = state.queue()
        counts = {"total": len(rows), "verified": sum(r["verified"] for r in rows), "rejected": sum(r["rejected"] for r in rows),
                  "disagree": sum(r["status"] == "disagree" for r in rows), "partial": sum(r["status"] == "partial" for r in rows),
                  "agree": sum(r["status"] == "agree" for r in rows)}
        return render("queue.html", rows=rows, counts=counts, records_dir=str(state.records_dir), only=state.only)

    @app.get("/r/{rid}", response_class=HTMLResponse)
    def record(rid: str, request: Request) -> HTMLResponse:
        packs = state.packets_for(rid)
        if not packs:
            raise HTTPException(404, f"no extracted packets for {rid}")
        agents = sorted(packs)
        want = request.query_params.get("from", "")
        base: dict | None = None
        if want == "B" and len(agents) > 1:
            base, from_agent = packs[agents[1]], "B"
        elif want == "A" or want not in ("draft", "") or state.existing_draft(rid) is None:
            base, from_agent = packs[agents[0]], "A"
        else:
            base, from_agent = state.existing_draft(rid), "draft"
        if base is None or "_invalid" in base:
            base = next((p for p in packs.values() if "_invalid" not in p), {})
        return render("record.html", **_record_ctx(rid, base, draft_form_values(base), [], from_agent))

    @app.get("/r/{rid}/next")
    def skip(rid: str) -> RedirectResponse:
        return _after(rid)

    async def _form(request: Request) -> dict[str, str]:
        f = await request.form()
        return {k: str(v) for k, v in f.items()}

    @app.post("/r/{rid}/promote")
    async def promote(rid: str, request: Request):
        form = await _form(request)
        draft, problems = form_to_draft(rid, form)
        if not problems:
            rec, problems = promote_record(state, rid, draft)
            if not problems:
                return _after(rid)
        return render("record.html", 400, **_record_ctx(rid, draft, _merge_form(form, draft), problems, form.get("from_agent", "A")))

    @app.post("/r/{rid}/draft")
    async def save_draft(rid: str, request: Request):
        form = await _form(request)
        draft, problems = form_to_draft(rid, form)
        if problems:
            return render("record.html", 400, **_record_ctx(rid, draft, _merge_form(form, draft), problems, form.get("from_agent", "A")))
        if not state.packets_for(rid):
            raise HTTPException(404, f"no extracted packets for {rid}")
        state.drafts.mkdir(parents=True, exist_ok=True)
        (state.drafts / f"{rid}.json").write_text(json.dumps(draft, indent=1, ensure_ascii=False) + "\n")
        return RedirectResponse(f"/r/{rid}?from=draft", status_code=303)

    @app.post("/r/{rid}/reject")
    async def reject(rid: str, request: Request):
        form = await _form(request)
        if not state.packets_for(rid):
            raise HTTPException(404, f"no extracted packets for {rid}")
        reason = (form.get("verification_notes") or "").strip()
        state.rejected.mkdir(parents=True, exist_ok=True)
        payload = {"id": rid, "reason": reason, "rejected_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (state.rejected / f"{rid}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
        return _after(rid)

    return app


def _merge_form(form: dict[str, str], draft: dict) -> dict[str, Any]:
    """Re-populate the form from what the owner submitted (raw JSON text kept verbatim so errors can be fixed)."""
    v = draft_form_values(draft)
    for k in ("estimates_json", "sources_json"):
        if k in form:
            v[k] = form[k]
    return v


# ----------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--records-dir", default=str(ROOT / "records"))
    ap.add_argument("--only", default="", help="comma-separated ids to restrict the queue to")
    ap.add_argument("--open", action="store_true", help="print the URL (no browser is launched)")
    args = ap.parse_args(argv)
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    url = f"http://127.0.0.1:{args.port}"
    if args.open:
        print(url, flush=True)
    app = create_app(Path(args.records_dir), only)
    import uvicorn

    print(f"Bedside Brief verification queue: {url}  (records: {args.records_dir})", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
