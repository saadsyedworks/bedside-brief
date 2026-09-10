"""tools/verify_ui.py: queue order, side-by-side record page, promote / reject / draft writes.

Uses a tmp records dir with two synthetic schema-valid packets per id (built from conftest helpers);
never touches the real records/ tree.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import EXAM, HX, SOURCE_RCE, stat, write_record
from tools.validate import validate_records
from tools.verify_ui import create_app, draft_form_values, source_url

DISAGREE_ID = HX["identity"]["id"]          # hx_exertional_syncope  (sorts after exam_* alphabetically)
AGREE_ID = EXAM["identity"]["id"]           # exam_late_peaking_murmur


def _packet(rec: dict, agent: str) -> dict:
    p = copy.deepcopy(rec)
    p.update({"tier": "extracted", "agent_id": agent, "verified_by": None, "verified_at": None})
    return p


@pytest.fixture
def vdir(tmp_path: Path) -> Path:
    records = tmp_path / "records"
    ext = records / "extracted"
    a, b = _packet(HX, "extractor-A"), _packet(HX, "extractor-B")
    b["estimates"][0]["sensitivity"] = stat(0.60, 0.5, 0.7)  # numeric mismatch -> disagree
    b["interpretation"]["pitfalls"] = "A different pitfall."
    write_record(ext, a, "__extractor-A")
    write_record(ext, b, "__extractor-B")
    write_record(ext, _packet(EXAM, "extractor-A"), "__extractor-A")
    write_record(ext, _packet(EXAM, "extractor-B"), "__extractor-B")
    (records / "redteam").mkdir()
    (records / "redteam" / "wave1.md").write_text(f"# wave 1\n- {AGREE_ID}: quote is not verbatim\n")
    return records


@pytest.fixture
def client(vdir: Path, tmp_path: Path) -> TestClient:
    return TestClient(create_app(vdir, ids_path=tmp_path / "no_ids.json"))


def _form(rec: dict, **over: str) -> dict[str, str]:
    f = {k: str(v) for k, v in draft_form_values(rec).items()}
    f["from_agent"] = "A"
    f.update(over)
    return f


def test_queue_orders_disagreements_first_and_shows_redteam(client: TestClient):
    r = client.get("/")
    assert r.status_code == 200
    assert r.text.index(f'href="/r/{DISAGREE_ID}"') < r.text.index(f'href="/r/{AGREE_ID}"')
    assert ">disagree<" in r.text and ">agree<" in r.text
    assert "wave1.md:2" in r.text and "quote is not verbatim" in r.text
    assert 'class="badge verified"' not in r.text


def test_record_page_shows_both_packets_flags_and_links(client: TestClient):
    r = client.get(f"/r/{DISAGREE_ID}")
    assert r.status_code == 200
    assert "extractor-A" in r.text and "extractor-B" in r.text
    assert "NUMERIC MISMATCH" in r.text
    assert "A different pitfall." in r.text and 'class="b diff"' in r.text
    assert f"https://pubmed.ncbi.nlm.nih.gov/{SOURCE_RCE['pmid']}/" in r.text
    assert 'name="estimates_json"' in r.text and 'name="verification_notes"' in r.text
    assert "draft from: <b>A</b>" in r.text
    assert "draft from: <b>B</b>" in client.get(f"/r/{DISAGREE_ID}?from=B").text
    assert client.get("/r/hx_does_not_exist").status_code == 404


def test_promote_writes_schema_valid_verified_file(client: TestClient, vdir: Path):
    r = client.post(f"/r/{DISAGREE_ID}/promote", data=_form(HX, verification_notes="Read Table 2; 85% confirmed."), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/r/{AGREE_ID}"
    out = vdir / "verified" / f"{DISAGREE_ID}.json"
    rec = json.loads(out.read_text())
    assert rec["tier"] == "verified" and rec["verified_by"] == "owner"
    assert rec["verified_at"].endswith("+00:00") and rec["record_version"] == 1
    assert rec["verification_notes"] == "Read Table 2; 85% confirmed."
    assert rec["estimates"][0]["sensitivity"]["value"] == 0.85
    errs, _ = validate_records(vdir / "verified")
    assert errs == []
    assert 'class="badge verified"' in client.get("/").text
    # promoting again bumps the version
    client.post(f"/r/{DISAGREE_ID}/promote", data=_form(HX), follow_redirects=False)
    assert json.loads(out.read_text())["record_version"] == 2
    for bad in ("rejected", "drafts"):
        assert not (vdir / bad).exists()


def test_promote_invalid_estimate_json_returns_400_and_writes_nothing(client: TestClient, vdir: Path):
    r = client.post(f"/r/{DISAGREE_ID}/promote", data=_form(HX, estimates_json='[{"target_condition": '), follow_redirects=False)
    assert r.status_code == 400 and "not valid JSON" in r.text
    assert not (vdir / "verified").exists()
    # schema-invalid but parseable: quantified with a stat lacking quote+location
    bad = copy.deepcopy(HX)
    bad["estimates"][0]["quote"] = ""
    r = client.post(f"/r/{DISAGREE_ID}/promote", data=_form(bad), follow_redirects=False)
    assert r.status_code == 400 and "quote+location" in r.text
    assert not (vdir / "verified").exists()


def test_promote_refuses_vocab_violating_differential(client: TestClient, vdir: Path):
    r = client.post(f"/r/{DISAGREE_ID}/promote", data=_form(HX, differentials="aortic_stenosis, made_up_dx"), follow_redirects=False)
    assert r.status_code == 400 and "differentials not in vocab" in r.text and "made_up_dx" in r.text
    assert not (vdir / "verified").exists()


def test_reject_writes_reason_file(client: TestClient, vdir: Path):
    r = client.post(f"/r/{AGREE_ID}/reject", data=_form(EXAM, verification_notes="Source table not accessible."), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"  # nothing unhandled after the last id
    rej = json.loads((vdir / "rejected" / f"{AGREE_ID}.json").read_text())
    assert rej["id"] == AGREE_ID and rej["reason"] == "Source table not accessible." and rej["rejected_at"].endswith("+00:00")
    assert not (vdir / "verified").exists()
    assert 'class="badge rejected"' in client.get("/").text


def test_edit_later_saves_draft_without_promoting(client: TestClient, vdir: Path):
    r = client.post(f"/r/{DISAGREE_ID}/draft", data=_form(HX, title="Exertional syncope (owner edit)"), follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/r/{DISAGREE_ID}?from=draft"
    d = json.loads((vdir / "drafts" / f"{DISAGREE_ID}.json").read_text())
    assert d["identity"]["title"] == "Exertional syncope (owner edit)" and d["tier"] == "extracted"
    assert not (vdir / "verified").exists()
    page = client.get(f"/r/{DISAGREE_ID}").text
    assert "draft from: <b>draft</b>" in page and "Exertional syncope (owner edit)" in page


def test_skip_and_only_filter(client: TestClient, vdir: Path, tmp_path: Path):
    r = client.get(f"/r/{DISAGREE_ID}/next", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == f"/r/{AGREE_ID}"
    only = TestClient(create_app(vdir, only=[AGREE_ID], ids_path=tmp_path / "no_ids.json"))
    q = only.get("/").text
    assert f'href="/r/{AGREE_ID}"' in q and f'href="/r/{DISAGREE_ID}"' not in q


def test_source_url_is_deterministic_and_guarded():
    assert source_url({"pmid": "9039886", "doi": "10.1/x"}) == "https://pubmed.ncbi.nlm.nih.gov/9039886/"
    assert source_url({"pmid": None, "doi": "10.1001/jama.277.7.564"}) == "https://doi.org/10.1001/jama.277.7.564"
    assert source_url({"pmid": "abc", "doi": "not a doi"}) is None
    assert source_url(None) is None
