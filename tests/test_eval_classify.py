from __future__ import annotations

import pytest

from eval.classify import MODES, classify, section_for

# 30 labelled items: (text, category, bedside under the default mode)
LABELLED = [
    ("Orthostatic vital signs (supine to standing at 1 and 3 min)", "functional", True),
    ("JVP", "exam", True),
    ("Ask about melena, hematemesis, and hematochezia", "history", True),
    ("Medication review (MAR): antihypertensives, opioids", "mar", True),
    ("Obtain a 12-lead ECG", "ecg", False),
    ("CT abdomen and pelvis with contrast", "imaging", False),
    ("Point-of-care ultrasound of the IVC and lung B-lines", "pocus", True),
    ("Bladder scan", "imaging", False),
    ("Point-of-care glucose", "lab", False),
    ("Check troponin", "lab", False),
    ("Surgical consult", "consult", False),
    ("Continuous telemetry", "monitoring", False),
    ("Pulse oximetry / SpO2", "monitoring", False),
    ("Admit to ICU", "disposition", False),
    ("Empiric broad-spectrum antibiotics", "treatment", False),
    ("IV fluid bolus 500 mL", "treatment", False),
    ("Blood pressure in both arms", "exam", True),
    ("Capillary refill time (>3 s)", "exam", True),
    ("Dix-Hallpike maneuver", "functional", True),
    ("HINTS exam", "functional", True),
    ("Witness account: duration, jerking", "history", True),
    ("Check blood glucose", "lab", False),
    ("Ask about urine output over the last 24 hours", "history", True),
    ("Strict intake and output", "monitoring", False),
    ("Lactate", "lab", False),
    ("Chest X-ray", "imaging", False),
    ("Passive leg raise", "functional", True),
    ("Bibasilar crackles", "exam", True),
    ("Prodrome and palpitations before the event", "history", True),
    ("Something entirely unrelated", "unclassified", False),
]


@pytest.mark.parametrize("text,category,bedside", LABELLED)
def test_labelled_items(text, category, bedside):
    c = classify(text)
    assert (c.category, c.bedside) == (category, bedside), c


def test_modes_flip_only_ecg_and_mar():
    assert classify("12-lead ECG", mode="ecg_bedside").bedside is True
    assert classify("12-lead ECG", mode="default").bedside is False
    assert classify("Medication review (MAR)", mode="mar_offbedside").bedside is False
    assert classify("Medication review (MAR)", mode="default").bedside is True
    for mode in MODES:  # everything else is mode-independent
        assert classify("Lactate", mode=mode).bedside is False
        assert classify("Murphy sign", mode=mode).bedside is True
    with pytest.raises(ValueError):
        classify("x", mode="nope")


def test_record_id_is_bedside_by_construction():
    for rid, cat in (("hx_exertional_syncope", "history"), ("exam_s3_gallop", "exam"), ("fn_orthostatic_vitals", "functional"), ("pocus_ivc_collapsibility", "pocus")):
        c = classify("Order a CT scan and labs", record_id=rid)  # text is ignored when an id is present
        assert c.bedside and c.category == cat and c.rule == "record_id"
    assert section_for("history") == "ask" and section_for("functional") == "examine" and section_for("lab") is None
