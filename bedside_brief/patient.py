"""Patient state read off the one-liner's own measurements.

`observed_values` carries what the clinician wrote, verbatim: "BP 88/54", "HR 118", "SpO2 88% on 4L".
This turns those into a small set of flags so a record's prose contraindication can be matched
against the patient in code, instead of every candidate arriving at the ranker with a hedge attached.

Nothing here interprets evidence or invents a value. It reads numbers the clinician supplied and
answers one question: could this record's `do_not_use_when` be about this patient?
"""
from __future__ import annotations

import re

# Deliberately narrow patterns. A missed measurement means a contraindication is not shown, which is
# the failure mode we can see in the metrics; a loose pattern would read a lab value as a blood
# pressure and hide or show the wrong thing silently.
_SBP = re.compile(r"\b(?:BP|SBP|systolic)\b[^0-9]{0,12}(\d{2,3})(?:\s*/\s*\d{2,3})?", re.I)
_HR = re.compile(r"\b(?:HR|pulse|heart\s*rate)\b[^0-9]{0,12}(\d{2,3})", re.I)
_SPO2 = re.compile(r"\b(?:SpO2|SaO2|O2\s*sat\w*|sat\w*)\b[^0-9]{0,12}(\d{2,3})\s*%?", re.I)
_TEMP = re.compile(r"\b(?:T|temp\w*)\b[^0-9]{0,12}(3\d(?:\.\d)?)\b", re.I)

# flag -> (test over the parsed values, phrases that mean a contraindication is about this flag)
_FLAGS: dict[str, tuple[str, object, tuple[str, ...]]] = {
    "hypotensive": ("sbp", lambda v: v < 90, ("hypotens", "shock", "low blood pressure", "haemodynamically unstable",
                                              "hemodynamically unstable", "unstable vital")),
    "bradycardic": ("hr", lambda v: v < 50, ("bradycard", "heart block", "slow heart")),
    "tachycardic": ("hr", lambda v: v > 120, ("tachycard", "rapid heart", "unstable vital")),
    "hypoxic": ("spo2", lambda v: v < 92, ("hypox", "desaturat", "respiratory distress", "oxygen requirement")),
    "febrile": ("temp", lambda v: v >= 38.0, ("febrile", "fever")),
}


def measurements(observed_values: list[str] | None) -> dict[str, float]:
    """{'sbp': 88.0, 'hr': 118.0, ...} for whatever the one-liner actually stated."""
    text = " ; ".join(observed_values or [])
    out: dict[str, float] = {}
    for key, pattern in (("sbp", _SBP), ("hr", _HR), ("spo2", _SPO2), ("temp", _TEMP)):
        m = pattern.search(text)
        if m:
            try:
                out[key] = float(m.group(1))
            except ValueError:
                pass
    return out


def flags(observed_values: list[str] | None) -> set[str]:
    """Which of the named states the stated measurements put this patient in."""
    vals = measurements(observed_values)
    return {name for name, (key, test, _) in _FLAGS.items() if key in vals and test(vals[key])}


def contraindication_applies(avoid_when: str | None, patient_flags: set[str]) -> bool:
    """Could this `do_not_use_when` be about a patient in these states?

    Errs towards False: a contraindication that names no state we can read from a measurement is not
    shown. That is the point of the narrow mode -- the alternative, attaching every record's caveat
    to every candidate, made the ranker cautious enough to cost ten points of perturbation
    responsiveness.
    """
    if not avoid_when or not patient_flags:
        return False
    low = avoid_when.lower()
    return any(phrase in low for name in patient_flags for phrase in _FLAGS[name][2])
