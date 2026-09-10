"""Deterministic bedside / off-bedside classifier for recommendation items.

Rubric (evaluation_rubric.md, "Scoring units"):
  bedside     = history question, exam maneuver, functional test, POCUS
  off-bedside = lab, imaging, ECG, consult, monitoring, admission/disposition, treatment
DECISIONS #11 / #18(4): medication review / MAR reconciliation = bedside HISTORY; SpO2,
telemetry, I/Os, weights, fluid-balance chart = MONITORING; POC glucose = lab, bladder scan =
imaging. ECG is off-bedside by default with an ECG-as-bedside sensitivity analysis.

`mode`: "default" (MAR bedside, ECG off-bedside) | "ecg_bedside" | "mar_offbedside".
Items that carry a record id are bedside by construction (every store record has bedside=true).

Rule order (first hit wins; written down once so the boundary is auditable):
  1 record id            -> category from the id prefix (hx_/exam_/fn_/pocus_)
  2 MAR / medication review
  3 leading history verb ("Ask ...", "History of ...", "Witness account ...")
  4 off-bedside: ecg, pocus-vs-imaging, lab, consult, monitoring, disposition, treatment
  5 bedside: pocus, functional, exam, history (keyword anywhere)
  6 otherwise "unclassified" (counted as NOT bedside; reported separately)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

MODES = ("default", "ecg_bedside", "mar_offbedside")
OFF_BEDSIDE = frozenset({"lab", "imaging", "ecg", "consult", "monitoring", "disposition", "treatment"})
BEDSIDE = frozenset({"history", "exam", "functional", "pocus", "mar"})
PREFIX_CATEGORY = {"hx": "history", "exam": "exam", "fn": "functional", "pocus": "pocus"}
SECTION_FOR_CATEGORY = {"history": "ask", "mar": "ask", "exam": "examine", "functional": "examine", "pocus": "pocus"}


def _rx(*terms: str) -> re.Pattern[str]:
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(terms) + r")(?![a-z0-9])", re.I)


MAR_RX = _rx(r"mar", r"medication (?:review|reconciliation|history|list|chart)", r"med(?:s|ication)? (?:rec|review)",
             r"review (?:the )?(?:mar|medications?|med list|drug chart)", r"reconcile medications?", r"drug (?:history|review)")
HISTORY_LEAD_RX = re.compile(
    r"^\W*(?:ask|asks|history|hx|witness|inquire|enquire|elicit|clarify|obtain (?:a |the )?(?:history|collateral)|collateral|"
    r"establish (?:the )?(?:time|last[- ]known)|confirm (?:timing|onset|the time)|take (?:a |the )?history|"
    r"question(?:s)? (?:about|the patient)|find out|determine (?:whether|if|when))\b", re.I)
ECG_RX = _rx(r"ecg", r"ekg", r"electrocardiogram", r"12[- ]lead", r"rhythm strip")
POCUS_RX = _rx(r"pocus", r"point[- ]of[- ]care (?:ultrasound|ultrasonography|echo)", r"bedside (?:ultrasound|ultrasonography|echo)",
               r"lung ultrasound", r"focused (?:cardiac )?ultrasound", r"fast exam", r"e-?fast", r"ivc (?:ultrasound|collapsibility)",
               r"b-lines", r"lung sliding")
IMAGING_RX = _rx(r"ct", r"cta", r"ctpa", r"mri", r"mra", r"x-?rays?", r"cxr", r"radiograph", r"ultrasound", r"ultrasonography", r"duplex",
                 r"doppler", r"echo(?:cardiogram|cardiography)?", r"tte", r"tee", r"imaging", r"scan", r"hida", r"v/q", r"angiogra(?:m|phy)",
                 r"bladder scan", r"kub", r"films?", r"sonogra(?:m|phy)")
LAB_RX = _rx(r"labs?", r"laboratory", r"cbc", r"bmp", r"cmp", r"chem(?:istry)?", r"electrolytes?", r"creatinine", r"bun", r"lactate",
             r"troponin", r"bnp", r"nt-probnp", r"d-?dimer", r"lipase", r"amylase", r"urinalysis", r"ua", r"cultures?", r"blood (?:test|work|count|gas|glucose|sugar|cultures?)",
             r"abg", r"vbg", r"ck", r"cpk", r"tsh", r"a1c", r"inr", r"pt/inr", r"coags?", r"coagulation", r"lft", r"liver (?:panel|function)", r"bilirubin", r"crp",
             r"esr", r"procalcitonin", r"hemoglobin", r"hematocrit", r"platelets?", r"wbc", r"white (?:cell|blood) count", r"glucose", r"fingerstick",
             r"point[- ]of[- ]care glucose", r"poc glucose", r"drug (?:screen|levels?)", r"toxicology", r"serum", r"urine (?:studies|sodium|electrolytes|dipstick|culture)",
             r"stool (?:test|testing|studies|culture|toxin|pcr)", r"c\.? ?diff(?:icile)? (?:test|testing|toxin|pcr)", r"cortisol", r"ammonia", r"magnesium", r"phosph(?:ate|orus)",
             r"blood type", r"type and (?:screen|cross)", r"ferritin", r"iron studies", r"cardiac enzymes", r"biomarkers?", r"arthrocentesis", r"joint aspiration",
             r"paracentesis", r"lumbar puncture", r"lp", r"biopsy", r"swab", r"pcr", r"serolog(?:y|ies)", r"thyroid (?:function|panel|tests?)")
CONSULT_RX = _rx(r"consult(?:ation)?s?", r"referral", r"refer", r"specialist", r"cardiology", r"neurology", r"surgery (?:team|consult)", r"surgical (?:consult|evaluation|review)",
                 r"call (?:the )?(?:surgeon|cardiologist|neurologist|gi|nephrology|urology|rapid response|the team)", r"stroke team", r"page")
MONITORING_RX = _rx(r"telemetry", r"cardiac monitor(?:ing)?", r"continuous (?:monitoring|pulse oximetry|ecg monitoring)", r"pulse ox(?:imetry)?", r"spo2", r"sao2",
                    r"oxygen saturation", r"o2 sat(?:uration)?s?", r"i/os?", r"ins and outs", r"intake and output", r"strict (?:i/o|input|intake)", r"urine output (?:monitoring|chart|trend)",
                    r"daily weights?", r"fluid balance", r"serial (?:vitals|measurements|monitoring|lactate)", r"holter", r"event monitor", r"ambulatory monitor(?:ing)?",
                    r"monitor(?:ing)? (?:vital|the patient|closely|for)", r"vital sign (?:trend|monitoring|chart)", r"chart review", r"flowsheet", r"nursing notes")
DISPOSITION_RX = _rx(r"admit(?:ted|ting|ssion)?", r"discharge", r"transfer", r"icu", r"intensive care", r"step-?down", r"escalat(?:e|ion)", r"rapid response", r"code (?:blue|stroke|status)",
                     r"stroke alert", r"level of care", r"disposition", r"observation unit", r"triage")
TREATMENT_RX = _rx(r"treat(?:ment|ing)?", r"therapy", r"give", r"administer", r"start(?:ing)?", r"initiate", r"prescribe", r"bolus", r"iv fluids?", r"fluid (?:bolus|resuscitation|challenge)",
                   r"antibiotics?", r"anticoagulat(?:e|ion|ant)", r"heparin", r"diure(?:se|sis|tics?)", r"furosemide", r"lasix", r"nitroglycerin", r"nitrates?", r"aspirin", r"analgesi[ac]",
                   r"morphine", r"opioids? (?:for|to)", r"oxygen (?:therapy|supplementation)", r"supplemental oxygen", r"o2 (?:therapy|supplementation)", r"niv", r"bipap", r"cpap", r"intubat(?:e|ion)",
                   r"adenosine", r"cardiovers(?:e|ion)", r"pacing", r"steroids? (?:for|to)", r"prednisone", r"haloperidol", r"benzodiazepine (?:for|to)", r"lorazepam", r"thrombolysis", r"tpa",
                   r"reversal", r"transfus(?:e|ion)", r"insulin (?:drip|infusion)", r"vasopressors?", r"pressors?", r"norepinephrine", r"epinephrine", r"restraints?", r"sedat(?:e|ion)", r"nebuliz(?:er|ed)",
                   r"bronchodilator", r"epley", r"canalith repositioning", r"compression stockings", r"leg elevation", r"enema", r"laxative", r"lactulose (?:dose|titration)", r"hold (?:the )?(?:diuretic|antihypertensive|medication)")
FUNCTIONAL_RX = _rx(r"orthostatic", r"postural", r"dix-?hallpike", r"hints", r"head impulse", r"test of skew", r"gait", r"walk(?:ing)? test", r"ambulat(?:e|ion)", r"sit-?to-?stand", r"chair rise",
                    r"valsalva", r"squat(?:-to-stand)?", r"passive leg raise", r"plr", r"single breath count", r"forced expiratory time", r"jolt accentuation", r"supine roll", r"epley test",
                    r"carotid sinus massage", r"months backward", r"digit span", r"attention test", r"ice-?pack test", r"tap(?:s|ping)? out", r"finger rub", r"cover test", r"romberg", r"timed up and go",
                    r"dynamic auscultation", r"provocation", r"maneuver", r"manoeuvre", r"stand(?:ing)? (?:heart rate|blood pressure|vitals)", r"walk unaided")
EXAM_RX = _rx(r"exam(?:ination|ine)?", r"inspect(?:ion)?", r"palpat(?:e|ion)", r"auscultat(?:e|ion)", r"percuss(?:ion)?", r"listen", r"look for", r"observe", r"assess", r"check", r"measure",
              r"tenderness", r"rigidity", r"guarding", r"rebound", r"murmur", r"gallop", r"s3", r"s4", r"rub", r"crackles?", r"rales", r"wheez(?:e|es|ing)", r"breath sounds", r"egophony", r"dullness",
              r"hyperresonance", r"jvp", r"jugular", r"reflux", r"edema", r"oedema", r"pulse", r"pulses", r"heart rate", r"blood pressure", r"bp", r"respiratory rate", r"temperature", r"vital signs?", r"vitals",
              r"capillary refill", r"mottling", r"extremities", r"skin", r"rash", r"jaundice", r"icterus", r"pallor", r"cyanosis", r"mucous membranes", r"axilla(?:e)?", r"turgor",
              r"mental status", r"orientation", r"delirium screen", r"cam", r"gcs", r"glasgow", r"pupils?", r"gaze", r"nystagmus", r"cranial nerve", r"drift", r"strength", r"power", r"reflex(?:es)?",
              r"babinski", r"plantar", r"tone", r"sensation", r"sensory", r"visual fields?", r"speech", r"language", r"dysarthria", r"aphasia", r"facial (?:symmetry|droop|weakness)", r"neuro(?:logic(?:al)?)? (?:exam|screen|assessment)",
              r"asterixis", r"tremor", r"thyroid", r"goiter", r"abdomen", r"abdominal", r"flank", r"cva", r"costovertebral", r"suprapubic", r"bladder", r"rectal", r"dre", r"stool (?:for )?blood",
              r"calf", r"circumference", r"homan", r"cord", r"wound", r"incision", r"line site", r"picc", r"catheter (?:site|inspection)", r"joint", r"effusion", r"range of motion", r"compartment", r"pressure points?",
              r"chest wall", r"trachea(?:l)?", r"subcutaneous emphysema", r"work of breathing", r"accessory muscle", r"stridor", r"pulsus paradoxus", r"heart sounds?", r"carotid", r"upstroke",
              r"sign", r"signs", r"stigmata", r"lesions?", r"petechiae", r"hematoma", r"mass", r"distension", r"ascites", r"fluid wave", r"hernia", r"sacral", r"sacrum", r"otoscop(?:y|e)", r"fundoscop(?:y|ic)",
              r"finding", r"findings", r"ptosis", r"cannon", r"apical", r"precordi(?:al|um)", r"lymph", r"nodes?", r"tongue", r"oral", r"fever", r"tachycardia", r"tachypnea", r"hypotension", r"hypoxia")
HISTORY_RX = _rx(r"symptoms?", r"onset", r"duration", r"timing", r"trigger(?:s|ed)?", r"prodrome", r"prior", r"previous", r"recent", r"family history", r"social history", r"alcohol", r"substance", r"stimulant",
                 r"caffeine", r"smoking", r"travel", r"exposure", r"contacts?", r"intake", r"appetite", r"vomiting", r"nausea", r"diarrhea", r"bowel", r"void(?:ing|ed)?", r"dysuria", r"hematuria", r"melena",
                 r"hematemesis", r"cough", r"sputum", r"hemoptysis", r"orthopnea", r"pnd", r"palpitations", r"chest pain", r"dyspnea", r"headache", r"baseline", r"function(?:al status)?", r"adherence",
                 r"last dose", r"last drink", r"last[- ]known[- ]well", r"time course", r"character", r"quality", r"radiation", r"relieving", r"aggravating", r"associated", r"context", r"what (?:happened|the patient was doing)",
                 r"history", r"collateral", r"nurse", r"family", r"chart", r"review of systems", r"ros", r"pain score", r"immobil(?:ity|ization)", r"surgery", r"cancer", r"vte", r"dvt", r"pe", r"anticoagulant use",
                 r"nsaid", r"aspirin use", r"diuretic use", r"medications?", r"drugs?", r"doses?", r"insulin", r"sulfonylurea", r"steroids?", r"comorbidit(?:y|ies)", r"risk factors?", r"wells")

_OFF_RULES = (("ecg", ECG_RX), ("lab", LAB_RX), ("consult", CONSULT_RX), ("monitoring", MONITORING_RX), ("disposition", DISPOSITION_RX), ("treatment", TREATMENT_RX))


@dataclass(frozen=True)
class Classification:
    category: str  # history | mar | exam | functional | pocus | lab | imaging | ecg | consult | monitoring | disposition | treatment | unclassified
    bedside: bool
    rule: str  # which rule fired (for audit)


def category_of(text: str, record_id: str | None = None) -> tuple[str, str]:
    """(category, rule) independent of mode."""
    if record_id:
        prefix = record_id.split("_", 1)[0]
        return PREFIX_CATEGORY.get(prefix, "exam"), "record_id"
    t = (text or "").strip()
    if not t:
        return "unclassified", "empty"
    if MAR_RX.search(t):
        return "mar", "mar"
    if HISTORY_LEAD_RX.search(t):
        return "history", "history_lead"
    if ECG_RX.search(t):
        return "ecg", "ecg"
    if POCUS_RX.search(t):
        return "pocus", "pocus"
    if IMAGING_RX.search(t):
        return "imaging", "imaging"
    for cat, rx in _OFF_RULES[1:]:
        if rx.search(t):
            return cat, cat
    if FUNCTIONAL_RX.search(t):
        return "functional", "functional"
    if EXAM_RX.search(t):
        return "exam", "exam"
    if HISTORY_RX.search(t):
        return "history", "history_keyword"
    return "unclassified", "no_rule"


def is_bedside(category: str, mode: str = "default") -> bool:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
    if category == "ecg":
        return mode == "ecg_bedside"
    if category == "mar":
        return mode != "mar_offbedside"
    return category in BEDSIDE


def classify(text: str, record_id: str | None = None, mode: str = "default") -> Classification:
    category, rule = category_of(text, record_id)
    return Classification(category=category, bedside=is_bedside(category, mode), rule=rule)


def section_for(category: str) -> str | None:
    """Card section an item of this category would occupy (None for off-bedside / unclassified)."""
    return SECTION_FOR_CATEGORY.get(category)
