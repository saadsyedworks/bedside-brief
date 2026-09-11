"""Unit tests for the deterministic patient-state gate."""
from __future__ import annotations

import pytest

from bedside_brief.patient import contraindication_applies, flags, measurements

ORTHOSTATIC = ("Do not attempt standing measurements in a patient who is already hypotensive, too dizzy "
               "or weak to stand safely, or has an unstable spine or pelvis; a patient too dizzy to "
               "stand counts as a positive test.")


@pytest.mark.parametrize("values, expected", [
    (["BP 88/54", "HR 118"], {"sbp": 88.0, "hr": 118.0}),
    (["BP 96/60"], {"sbp": 96.0}),
    (["pulse 118"], {"hr": 118.0}),
    (["SpO2 88% on 4L"], {"spo2": 88.0}),
    (["T 38.6"], {"temp": 38.6}),
    (["Cr 1.1 to 2.0"], {}),          # a lab is not a vital sign
    ([], {}),
    (None, {}),
])
def test_measurements_read_only_what_the_clinician_wrote(values, expected):
    assert measurements(values) == expected


@pytest.mark.parametrize("values, expected", [
    (["BP 88/54"], {"hypotensive"}),
    (["BP 120/80"], set()),
    (["HR 42"], {"bradycardic"}),
    (["HR 118"], set()),              # 118 is not >120; the thresholds are deliberately conservative
    (["HR 132"], {"tachycardic"}),
    (["SpO2 88%"], {"hypoxic"}),
    (["T 38.6"], {"febrile"}),
    (["BP 84/50", "SpO2 89%"], {"hypotensive", "hypoxic"}),
])
def test_flags(values, expected):
    assert flags(values) == expected


def test_the_case_the_gate_exists_for():
    """hypotension_002: supine 88/54, and the record says do not stand an already-hypotensive patient."""
    assert contraindication_applies(ORTHOSTATIC, flags(["BP 88/54", "HR 118"])) is True


def test_unrelated_contraindication_is_hidden():
    assert contraindication_applies("Do not percuss over a recent abdominal incision.",
                                    flags(["BP 88/54"])) is False


def test_no_measurements_means_nothing_is_shown():
    """Errs towards hiding: with no readable measurement the narrow mode shows no caveat at all."""
    assert contraindication_applies(ORTHOSTATIC, flags([])) is False
    assert contraindication_applies(ORTHOSTATIC, set()) is False
    assert contraindication_applies(None, {"hypotensive"}) is False
