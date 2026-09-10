"""Deterministic card rendering from stored record fields only.

Everything on an item comes from the verified record. The only LLM-authored strings
(rationale, chief complaint, missing features) pass through `strip_numbers`, so the LLM
can never put a number on a card. Numbers are formatted with `normalise_number`, the same
canonical form the validator compares against.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from jinja2 import Environment

import config
from bedside_brief.retrieve import SECTION_TYPES
from bedside_brief.validate import normalise_number

log = logging.getLogger("bedside_brief.render")

Card = dict[str, Any]
COPY_LINE = "Review. Pocket the phone. See the patient."
_DIGITS = re.compile(r"\d+")


def strip_numbers(text: str | None) -> str:
    """Replace every digit run with "[n]" so LLM text can never carry a number."""
    return _DIGITS.sub("[n]", text or "")


def _num(value: Any) -> str | None:
    return None if value is None else normalise_number(value)


def _stat(stat: dict[str, Any] | None) -> dict[str, str | None] | None:
    if not stat:
        return None
    return {"value": _num(stat.get("value")), "ci_low": _num(stat.get("ci_low")), "ci_high": _num(stat.get("ci_high"))}


def _estimate_view(estimate: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    idx = estimate.get("source_index")
    source = sources[idx] if isinstance(idx, int) and 0 <= idx < len(sources) else {}
    return {
        "target_condition": estimate.get("target_condition"),
        "population": estimate.get("population"),
        "setting": estimate.get("setting"),
        "reference_standard": estimate.get("reference_standard"),
        "prevalence": _num(estimate.get("prevalence")),
        "sensitivity": _stat(estimate.get("sensitivity")),
        "specificity": _stat(estimate.get("specificity")),
        "lr_positive": _stat(estimate.get("lr_positive")),
        "lr_negative": _stat(estimate.get("lr_negative")),
        "interpretation_label": estimate.get("interpretation_label"),
        "evidence_level": estimate.get("evidence_level"),
        "computed": bool(estimate.get("computed", False)),
        "quote": estimate.get("quote"),
        "location": estimate.get("location"),
        "citation": source.get("citation"),
        "kind": source.get("kind"),
        "year": _num(source.get("year")),
        "doi": source.get("doi"),
        "pmid": source.get("pmid"),
        "url": source.get("url"),
    }


def render_item(record: dict[str, Any], rationale: str | None = "") -> dict[str, Any]:
    """One card item, assembled only from the record's stored fields (+ stripped rationale)."""
    identity, technique = record["identity"], record["technique"]
    interp, safety = record["interpretation"], record.get("safety_scope", {})
    sources = record.get("sources", [])
    rid = identity["id"]
    return {
        "id": rid,
        "type": identity["type"],
        "title": identity["title"],
        "how": technique["how"],
        "prerequisites": technique.get("prerequisites") or None,
        "contraindications": technique.get("contraindications") or None,
        "positive_finding": interp["positive_finding"],
        "negative_finding": interp["negative_finding"],
        "changes_what": interp["changes_what"],
        "pitfalls": interp.get("pitfalls") or None,
        "do_not_use_when": safety.get("do_not_use_when") or None,
        "skill_assumption": safety.get("skill_assumption") or None,
        "escalation_warning": safety.get("escalation_warning") or None,
        "evidence_badge": record["evidence_status"],
        "evidence": [_estimate_view(e, sources) for e in record.get("estimates", [])],
        "rationale": strip_numbers(rationale),
        "audit_link": f"/record/{rid}",
    }


def render_card(
    chosen: dict[str, list[dict[str, Any]]],
    records_by_id: dict[str, dict[str, Any]],
    parsed: dict[str, Any],
    limits: Any = config,
) -> Card:
    """Card from the ranker's `chosen` ids. Unknown, unverified, or wrong-section ids are
    skipped (logged); sections are truncated to the limits; pocus is dropped when disabled."""
    card: Card = {
        "presentation": parsed.get("presentation"),
        "chief_complaint": strip_numbers(parsed.get("chief_complaint")),
        "sections": {},
    }
    # Ask-first renders only when the parser declared the input underspecified (DECISIONS #29);
    # a non-empty missing_features list alone is not enough (legacy parses without the flag still work).
    missing = [strip_numbers(m) for m in parsed.get("missing_features") or [] if m]
    if missing and parsed.get("underspecified", True):
        card["ask_first"] = missing
    caps = {"ask": limits.MAX_ASK, "examine": limits.MAX_EXAMINE, "pocus": limits.MAX_POCUS}
    for section, types in SECTION_TYPES.items():
        if section == "pocus" and not limits.POCUS_ENABLED:
            continue
        items: list[dict[str, Any]] = []
        for choice in chosen.get(section) or []:
            if len(items) >= caps[section]:
                break
            rid = choice.get("id")
            record = records_by_id.get(rid)
            if record is None or record.get("tier") not in config.RENDER_TIERS:
                log.warning("render: %s/%s skipped (not a verified record)", section, rid)
                continue
            if record["identity"]["type"] not in types:
                log.warning("render: %s/%s skipped (type %s not allowed in section)", section, rid, record["identity"]["type"])
                continue
            items.append(render_item(record, choice.get("rationale")))
        card["sections"][section] = items
    return card


# --- HTML (single page, no chat transcript; no digits in chrome) --------------------------
_SECTION_LABELS = {"ask": "ASK", "examine": "EXAMINE", "pocus": "POCUS"}

_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bedside Brief</title>
<style>
body{font-family:system-ui,sans-serif;max-width:52rem;margin:0 auto;padding:1rem;line-height:1.4;color:#111;background:#fff}
form{display:flex;gap:.5rem;margin-bottom:1rem}input[type=text]{flex:1;padding:.6rem;font-size:1rem}
button{padding:.6rem 1rem;font-size:1rem}.copy{font-style:italic;color:#444;margin:.5rem 0 1rem}
h2{border-bottom:1px solid #ccc;padding-bottom:.2rem;margin-top:1.5rem}.item{margin:.75rem 0;padding:.5rem .75rem;border-left:3px solid #888}
.badge{font-size:.8rem;padding:.1rem .4rem;border-radius:.3rem;background:#eee;margin-left:.5rem}
.badge.quantified{background:#d7f5dd}.badge.partially_quantified{background:#fff1c2}.badge.not_quantified{background:#eee}
.how{margin:.25rem 0}.rationale{color:#555}.ask-first{background:#fff1c2;padding:.5rem .75rem;margin:.75rem 0}
.blocked{background:#fde2e2;padding:.5rem .75rem;margin:.75rem 0}details{margin-top:.4rem}summary{cursor:pointer}
.est{margin:.4rem 0 .4rem 1rem;font-size:.9rem}.audit{font-size:.8rem}
</style></head><body>
<h1>Bedside Brief</h1>
<form method="post" action="{{ action }}">
<input type="text" name="oneliner" placeholder="Patient one-liner" value="{{ oneliner }}" autofocus>
<button type="submit">Brief me</button>
</form>
<p class="copy">{{ copy_line }}</p>
{% if card %}
{% if card.chief_complaint %}<p><strong>Chief complaint:</strong> {{ card.chief_complaint }}{% if card.presentation %} <em>({{ card.presentation }})</em>{% endif %}</p>{% endif %}
{% if card.ask_first %}<div class="ask-first"><strong>Ask first:</strong> {{ card.ask_first | join("; ") }}</div>{% endif %}
{% if card.blocked %}<div class="blocked"><strong>Withheld:</strong> {{ card.blocked.note }}</div>{% endif %}
{% for section, items in card.sections.items() %}
<h2>{{ labels[section] }}</h2>
{% if not items %}<p><em>Nothing verified for this section.</em></p>{% endif %}
{% for it in items %}
<div class="item">
<div><strong>{{ it.title }}</strong><span class="badge {{ it.evidence_badge }}">{{ it.evidence_badge | replace("_", " ") }}</span></div>
<div class="how">{{ it.how }}</div>
<div><strong>Positive:</strong> {{ it.positive_finding }}</div>
<div><strong>Negative:</strong> {{ it.negative_finding }}</div>
<div><strong>Changes:</strong> {{ it.changes_what }}</div>
{% if it.pitfalls %}<div><strong>Pitfalls:</strong> {{ it.pitfalls }}</div>{% endif %}
{% if it.do_not_use_when %}<div><strong>Do not use when:</strong> {{ it.do_not_use_when }}</div>{% endif %}
{% if it.skill_assumption %}<div><strong>Skill assumed:</strong> {{ it.skill_assumption }}</div>{% endif %}
{% if it.rationale %}<div class="rationale">Why here: {{ it.rationale }}</div>{% endif %}
<details><summary>Evidence</summary>
{% if not it.evidence %}<p class="est">Not quantified in the cited source; use is guideline or consensus based.</p>{% endif %}
{% for e in it.evidence %}
<div class="est">
<div><strong>{{ e.target_condition }}</strong> — {{ e.population }}{% if e.setting %}, {{ e.setting }}{% endif %}{% if e.evidence_level %} [{{ e.evidence_level | replace("_", " ") }}]{% endif %}</div>
{% if e.prevalence %}<div>Prevalence {{ e.prevalence }}</div>{% endif %}
{% for name, st in (("Sensitivity", e.sensitivity), ("Specificity", e.specificity), ("LR+", e.lr_positive), ("LR−", e.lr_negative)) %}
{% if st %}<div>{{ name }} {{ st.value }}{% if st.ci_low and st.ci_high %} (CI {{ st.ci_low }}–{{ st.ci_high }}){% endif %}</div>{% endif %}
{% endfor %}
{% if e.computed %}<div><em>Computed from the source's two-by-two table.</em></div>{% endif %}
{% if e.quote %}<div>“{{ e.quote }}”{% if e.location %} — {{ e.location }}{% endif %}</div>{% endif %}
<div>{{ e.citation }}{% if e.year %} ({{ e.year }}){% endif %}{% if e.doi %} · DOI {{ e.doi }}{% endif %}{% if e.pmid %} · PMID {{ e.pmid }}{% endif %}</div>
</div>
{% endfor %}
<div class="audit"><a href="{{ it.audit_link }}">Audit record</a></div>
</details>
</div>
{% endfor %}
{% endfor %}
{% endif %}
</body></html>
"""

_env = Environment(autoescape=True)
_page = _env.from_string(_TEMPLATE)


def render_html(card: Card | None, oneliner: str = "", action: str = "/brief") -> str:
    """Single-page UI: input box, one button, ASK / EXAMINE / (POCUS), evidence on demand."""
    return _page.render(card=card, oneliner=oneliner, action=action, copy_line=COPY_LINE, labels=_SECTION_LABELS)
