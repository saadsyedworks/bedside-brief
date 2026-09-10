"""One-liner -> strict, vocab-bound JSON. The LLM is asked for exactly one kind of number
(differential weights); every other string it returns is digit-stripped in code.

Any presentation, differential or tag outside vocab.json raises `ParserVocabError`
(never silently dropped) so a vocabulary drift is loud and auditable.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import config
from bedside_brief.render import strip_numbers
from bedside_brief.store import DIFFERENTIALS, PRESENTATIONS, TAGS

log = logging.getLogger("bedside_brief.parser")


class ParserError(ValueError):
    """Reply violates the parser contract (e.g. no differentials)."""


class ParserVocabError(ParserError):
    """Reply used a presentation / differential / tag that is not in vocab.json."""


_STRING_ARRAY = {"type": "array", "items": {"type": "string"}}
PARSER_SCHEMA: dict[str, Any] = {
    "title": "oneliner_parse",
    "type": "object",
    "additionalProperties": False,
    "required": ["chief_complaint", "presentation", "time_course", "modifiers", "differentials", "indication_tags", "missing_features", "underspecified"],
    "properties": {
        "chief_complaint": {"type": "string"},
        "presentation": {"type": "string"},
        "time_course": {"type": "string"},
        "modifiers": _STRING_ARRAY,
        "differentials": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["dx", "weight"],
                "properties": {"dx": {"type": "string"}, "weight": {"type": "number"}},
            },
        },
        "indication_tags": _STRING_ARRAY,
        "missing_features": _STRING_ARRAY,
        "underspecified": {"type": "boolean"},
    },
}


def _vocab() -> dict[str, Any]:
    return json.loads(Path(config.VOCAB_PATH).read_text())


def system_prompt() -> str:
    vocab = _vocab()
    lines = [
        "You parse an inpatient internal-medicine one-liner into a strict JSON object for a bedside decision-support tool.",
        "Emit ONLY the strings listed below for presentation, differentials and indication_tags; any other string is rejected.",
        "Do not emit sensitivities, specificities, likelihood ratios, citations, or any number other than the differential weights.",
        "",
        "PRESENTATIONS and the differentials allowed under each (a differential may be used under any presentation):",
    ]
    for pres, dxs in vocab["presentations"].items():
        lines.append(f"- {pres}: {', '.join(dxs)}")
    lines += [
        "",
        "INDICATION_TAGS: " + ", ".join(vocab["indication_tags"]),
        "",
        "Fields:",
        "- chief_complaint: short paraphrase, no numbers.",
        "- presentation: exactly one PRESENTATION key.",
        "- time_course: e.g. hyperacute / acute / subacute / chronic, in words.",
        "- modifiers: short qualifying phrases from the one-liner (no numbers).",
        f"- differentials: one to {config.MAX_DIFFERENTIALS} entries, each {{dx, weight}} with weight in [0, 1], most likely first, weights descending.",
        "- indication_tags: zero or more INDICATION_TAGS that apply.",
        "- underspecified: judge the PRESENTING COMPLAINT, not the patient background. True when the complaint itself is "
        "uncharacterised: no onset or time course of the symptom, no trigger or positional/exertional context, and no character "
        "or localisation - so you cannot rank the differentials better than the base rate for that presentation. "
        "Age, ward, admission diagnosis, comorbidity, devices and routine vitals are BACKGROUND: they do not make a vague "
        "complaint specified. False as soon as the complaint itself carries an onset, a trigger, a character, a localisation, "
        "or an associated symptom, even if much else is unknown.",
        "Example true: '80M admitted yesterday for cellulitis, nurse says he seems off tonight, no other details' "
        "(rich background, but 'off' is uncharacterised). "
        "Example false: '58F post-op day 1, sudden sharp pain worse on inspiration' (onset, character and trigger given).",
        "- missing_features: ONLY when underspecified is true, list the 1-3 HISTORY questions that would characterise the complaint. "
        "Never list exam findings, labs, or imaging here; when underspecified is false this must be an empty list.",
        "Reply with the JSON object only.",
    ]
    return "\n".join(lines)


def _check_vocab(reply: dict[str, Any]) -> None:
    bad: list[str] = []
    if reply["presentation"] not in PRESENTATIONS:
        bad.append(f"presentation {reply['presentation']!r}")
    for d in reply["differentials"]:
        if d["dx"] not in DIFFERENTIALS:
            bad.append(f"differential {d['dx']!r}")
    for t in reply["indication_tags"]:
        if t not in TAGS:
            bad.append(f"indication_tag {t!r}")
    if bad:
        raise ParserVocabError("not in vocab.json: " + "; ".join(bad))


def _normalise_differentials(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clamp to [0,1], dedupe (keep the highest weight), sort descending, truncate, rescale so max == 1."""
    best: dict[str, float] = {}
    for d in items:
        w = min(1.0, max(0.0, float(d["weight"])))
        best[d["dx"]] = max(w, best.get(d["dx"], 0.0))
    ordered = sorted(best.items(), key=lambda kv: -kv[1])[: config.MAX_DIFFERENTIALS]
    if not ordered:
        raise ParserError("parser returned no differentials")
    top = ordered[0][1] or 1.0
    return [{"dx": dx, "weight": round(w / top, 3) if top else 1.0} for dx, w in ordered]


def parse_oneliner(text: str, llm: Any) -> dict[str, Any]:
    """LLM parse + code-side contract enforcement. Output keys match the retrieve/render contract."""
    if not (text or "").strip():
        raise ParserError("empty one-liner")
    reply = llm.complete_json(system_prompt(), text.strip(), PARSER_SCHEMA)
    try:
        _check_vocab(reply)
    except ParserVocabError as first:
        # One corrective re-parse with the violation fed back; still rejected if it repeats (never silently dropped).
        log.warning("vocab violation, re-parsing once: %s", first)
        feedback = (
            f"{text.strip()}\n\n[CORRECTION] Your previous answer used strings that are NOT in the vocabulary: {first}. "
            "Re-emit the full JSON using ONLY the listed strings; if no listed indication_tag applies, return an empty list."
        )
        reply = llm.complete_json(system_prompt(), feedback, PARSER_SCHEMA)
        _check_vocab(reply)
    parsed = {
        "chief_complaint": strip_numbers(reply["chief_complaint"]),
        "presentation": reply["presentation"],
        "time_course": strip_numbers(reply["time_course"]),
        "modifiers": [strip_numbers(m) for m in reply["modifiers"] if m],
        "differentials": _normalise_differentials(reply["differentials"]),
        "indication_tags": list(dict.fromkeys(reply["indication_tags"])),
        "underspecified": bool(reply.get("underspecified", False)),
        "missing_features": [strip_numbers(m) for m in reply["missing_features"] if m] if reply.get("underspecified") else [],
    }
    log.info(
        "parsed presentation=%s differentials=%d tags=%d underspecified=%s missing_features=%d",
        parsed["presentation"], len(parsed["differentials"]), len(parsed["indication_tags"]), parsed["underspecified"], len(parsed["missing_features"]),
    )
    return parsed
