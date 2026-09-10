from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import config
from bedside_brief import store
from bedside_brief.api import app
from bedside_brief.llm import FakeLLM
from tests.test_pipeline import PARSE, RANK


@pytest.fixture
def client(records_dir):
    store.build_index(config.DB_PATH, tiers=("verified", "extracted"))  # extracted indexed so /record can refuse it
    app.state.llm = FakeLLM([PARSE, RANK])
    with TestClient(app) as c:
        yield c
    app.state.llm = None


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200 and "Brief me" in r.text and 'name="oneliner"' in r.text
    assert "Pocket the phone" in r.text


def test_post_brief_returns_card(client):
    r = client.post("/brief", data={"oneliner": "65M syncope on stairs"})
    assert r.status_code == 200
    assert "ASK" in r.text and "EXAMINE" in r.text and "Late-peaking systolic murmur" in r.text
    assert 'href="/record/exam_late_peaking_murmur"' in r.text
    assert "[n]M syncope on stairs" in r.text  # chief complaint digit-stripped
    assert "Withheld" not in r.text


def test_record_audit_link(client):
    ok = client.get("/record/hx_exertional_syncope")
    assert ok.status_code == 200 and ok.json()["tier"] == "verified" and ok.json()["identity"]["id"] == "hx_exertional_syncope"
    assert client.get("/record/hx_positional_vertigo").status_code == 404  # extracted only
    assert client.get("/record/ghost").status_code == 404


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "fake-model" and body["records"]["verified"] == 4 and body["records"]["total"] == 5


def test_containment_failure_is_withheld_not_guessed(records_dir):
    store.build_index(config.DB_PATH)
    app.state.llm = FakeLLM([PARSE, dict(RANK, ask=[{"id": "hx_hallucinated", "rationale": "x"}])])
    with TestClient(app) as c:
        r = c.post("/brief", data={"oneliner": "65M syncope"})
    app.state.llm = None
    assert r.status_code == 502 and "Withheld" in r.text and "Late-peaking" not in r.text
