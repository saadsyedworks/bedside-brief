"""Deterministic item parser: arm C free text -> item list; the same enrichment is applied
to A/B card items (already structured) for symmetry.

Numbers come from `bedside_brief.validate.scan_numbers` (the store's single source of truth
for what counts as a number); a subset near performance words (sensitivity, LR, ...) is
kept as `performance_claims`. Citations: PMID / DOI / "et al" / journal-year / author-year.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from bedside_brief.validate import scan_numbers
from eval.classify import classify

_BULLET = re.compile(r"^\s*(?:[-*•‣◦▪>]+|\(?\d{1,2}[.):]|\(?[a-zA-Z][.)]|[ivx]{1,4}[.)])\s+", re.I)
_MD = re.compile(r"(\*\*|__|`|~~|^#+\s*)")
_HEADER = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?([A-Za-z][A-Za-z /&()-]{1,60}?)(?:\*\*)?\s*:\s*$")
_SKIP_LEAD = ("given ", "here are", "here is", "note:", "disclaimer", "in summary", "summary:", "these ", "this ", "overall,", "i would", "i'd", "as an ai", "remember")
_PERF = re.compile(r"sensitiv|specific|likelihood ratio|\blr[+\-−]?\b|\bppv\b|\bnpv\b|predictive value|accuracy|\bauc\b|odds ratio|c-statistic|pooled|meta-analys|%", re.I)
_CLAUSE_SPLIT = re.compile(r"(?<!\d)\.(?!\d)|;|\n|\band\b")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")
_CITE_PATTERNS = (
    ("pmid", re.compile(r"\bPMID\s*:?\s*\d{5,9}\b", re.I)),
    ("doi", re.compile(r"\b(?:doi\s*:?\s*|https?://doi\.org/)10\.\d{4,9}/\S+", re.I)),
    ("et_al", re.compile(r"\b[A-Z][A-Za-z'\-]+(?:\s+[A-Z]{1,3})?,?\s+et al\.?(?:,?\s*\(?(?:19|20)\d{2}\)?)?")),
    ("journal_year", re.compile(r"\b(?:JAMA|N(?:ew)? Engl(?:and)? J(?:ournal)? (?:of )?Med(?:icine)?|NEJM|Lancet|BMJ|Ann(?:als)? (?:of )?Intern(?:al)? Med(?:icine)?|Circulation|Chest|"
                                 r"Ann(?:als)? (?:of )?Emerg(?:ency)? Med(?:icine)?|Acad(?:emic)? Emerg(?:ency)? Med(?:icine)?|Stroke|Cochrane|Rational Clinical Examination|Am(?:erican)? J(?:ournal)? (?:of )?\w+)"
                                 r"\b[^.;\n]{0,40}?\b(?:19|20)\d{2}\b", re.I)),
    ("author_year", re.compile(r"\(\s*[A-Z][A-Za-z'\-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-z'\-]+)?,?\s+(?:19|20)\d{2}[a-z]?\s*\)")),
    ("named_study", re.compile(r"\b(?:McGee|Simel|Wells|Kimberly|HINTS|REVERT|Ottawa|San Francisco Syncope|Canadian Syncope|PERC)\b[^.;\n]{0,30}?(?:study|rule|criteria|score|series|meta-analysis)", re.I)),
)


@dataclass
class Item:
    text: str
    record_id: str | None = None
    section: str | None = None  # ask | examine | pocus for A/B; header context for C (history/exam/tests/...) or None
    bedside: bool = False
    category: str = "unclassified"
    numeric_claims: list[str] = field(default_factory=list)
    performance_claims: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def strip_formatting(text: str) -> str:
    """Bullets, numbering, markdown emphasis, collapsed whitespace."""
    t = _BULLET.sub("", text or "")
    t = _MD.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def detect_citations(text: str) -> list[str]:
    found: list[str] = []
    for _, rx in _CITE_PATTERNS:
        for m in rx.finditer(text or ""):
            s = m.group(0).strip()
            if s not in found:
                found.append(s)
    return found


def performance_numbers(text: str) -> list[str]:
    """Numbers that sit in a clause mentioning diagnostic-performance words (or carry a %)."""
    out: list[str] = []
    for clause in _CLAUSE_SPLIT.split(text or ""):
        if _PERF.search(clause):
            for n in sorted(scan_numbers(clause)):
                if n not in out and not _YEAR.match(n):
                    out.append(n)
    return out


def enrich(text: str, record_id: str | None = None, section: str | None = None, mode: str = "default") -> Item:
    """One item (already split) -> Item with classification, numbers and citations."""
    clean = strip_formatting(text)
    c = classify(clean, record_id, mode)
    return Item(
        text=clean, record_id=record_id, section=section, bedside=c.bedside, category=c.category,
        numeric_claims=sorted(scan_numbers(clean)), performance_claims=performance_numbers(clean), citations=detect_citations(clean),
    )


def _header_context(label: str) -> str | None:
    l = label.lower()
    if "history" in l or "ask" in l or "question" in l:
        return "history"
    if "exam" in l or "physical" in l:
        return "exam"
    if "bedside" in l or "point-of-care" in l or "pocus" in l:
        return "bedside_tests"
    if "test" in l or "lab" in l or "imaging" in l or "invest" in l or "work" in l:
        return "tests"
    if "diagnos" in l or "performance" in l or "evidence" in l or "data" in l:
        return "performance"
    return l[:30] or None


def _is_evidence_clause(piece: str) -> bool:
    """A ';'-separated fragment that only carries performance data / a citation for the
    preceding item (no bedside/off-bedside rule fires) is glued back onto that item."""
    return classify(piece).category == "unclassified" and bool(scan_numbers(piece) or detect_citations(piece) or piece[:1].islower())


def split_items(text: str) -> list[tuple[str, str | None]]:
    """Free text -> [(item_text, header_context)]. Splits on newlines, bullets, semicolons;
    drops headers, empty lines, and prose lead-ins (see _SKIP_LEAD). One-word lines are kept
    only when bulleted/numbered (e.g. "- Lactate")."""
    out: list[tuple[str, str | None]] = []
    context: str | None = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        h = _HEADER.match(line)
        if h:
            context = _header_context(h.group(1))
            continue
        bulleted = bool(_BULLET.match(line))
        # inline "Label: item" at the start of a line sets context and keeps the remainder
        m = re.match(r"^\s*(?:[-*•]\s*)?(?:\*\*)?(History|Physical exam(?:ination)?|Exam(?:ination)?|Bedside tests?|Tests?|Investigations?)(?:\*\*)?\s*:\s*(.+)$", line, re.I)
        if m:
            context = _header_context(m.group(1))
            line = m.group(2)
        line = strip_formatting(line)
        if not line or (len(line.split()) < 2 and not bulleted):
            continue
        if line.lower().startswith(_SKIP_LEAD):
            continue
        pieces: list[str] = []
        for piece in re.split(r";\s+", line):
            piece = strip_formatting(piece).rstrip(".")
            if not piece:
                continue
            if pieces and _is_evidence_clause(piece):
                pieces[-1] = pieces[-1] + "; " + piece
            else:
                pieces.append(piece)
        out.extend((p, context) for p in pieces)
    return out


def parse_free_text(text: str, mode: str = "default") -> list[Item]:
    """Arm C: raw completion -> items."""
    return [enrich(t, None, ctx, mode) for t, ctx in split_items(text)]


def items_from_card(card: dict[str, Any], mode: str = "default") -> list[Item]:
    """Arms A/B: one Item per card item (title = the item text; numbers = every number the
    rendered item displays, i.e. what the validator scanned)."""
    from bedside_brief.validate import _numbers_in  # same scanner as the validator

    items: list[Item] = []
    for section, entries in (card.get("sections") or {}).items():
        for entry in entries:
            it = enrich(entry.get("title", ""), entry.get("id"), section, mode)
            it.numeric_claims = sorted(_numbers_in(entry))
            it.performance_claims = sorted(
                n for e in entry.get("evidence") or [] for st in (e.get("sensitivity"), e.get("specificity"), e.get("lr_positive"), e.get("lr_negative"))
                if st for n in (st.get("value"), st.get("ci_low"), st.get("ci_high")) if n
            )
            it.citations = sorted({e["citation"] for e in entry.get("evidence") or [] if e.get("citation")})
            items.append(it)
    return items
