"""FastAPI app: one page, one button, an audit link per item. No chat, no session state.

    uvicorn bedside_brief.api:app

Startup resolves the model with a one-token call (falls back per config) and builds the
SQLite index if it does not exist. Tests inject a FakeLLM via `app.state.llm` before the
lifespan runs, so nothing here needs a key offline.
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

import config
from bedside_brief import store
from bedside_brief.llm import LLMClient
from bedside_brief.parser import ParserError
from bedside_brief.pipeline import brief
from bedside_brief.rank import RankerContainmentError
from bedside_brief.render import render_html

log = logging.getLogger("bedside_brief.api")


def _db_path() -> Path:
    return Path(config.DB_PATH)


def _ensure_index() -> None:
    if not _db_path().exists():
        store.build_index(_db_path())


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_index()
    if getattr(app.state, "llm", None) is None:
        try:
            client = LLMClient()
            client.startup_check()
            app.state.llm = client
        except Exception as exc:  # app still serves the page and /health; /brief reports unavailability
            log.error("LLM unavailable at startup: %s", type(exc).__name__)
            app.state.llm = None
    yield


app = FastAPI(title="Bedside Brief", lifespan=lifespan)
app.state.llm = None


def _record_counts() -> dict[str, int]:
    _ensure_index()
    with sqlite3.connect(_db_path()) as con:
        rows = con.execute("SELECT tier, COUNT(*) FROM records GROUP BY tier").fetchall()
    counts = {tier: n for tier, n in rows}
    counts["total"] = sum(counts.values())
    return counts


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return render_html(None)


@app.post("/brief", response_class=HTMLResponse)
def post_brief(oneliner: str = Form(..., min_length=1)) -> HTMLResponse:
    llm = app.state.llm
    if llm is None:
        return HTMLResponse(render_html(_withheld("Model unavailable; check the key and model in config."), oneliner), status_code=503)
    try:
        result = brief(oneliner, llm, _db_path())
    except (ParserError, RankerContainmentError) as exc:
        log.warning("brief blocked: %s: %s", type(exc).__name__, exc)
        return HTMLResponse(render_html(_withheld("The model reply failed the vocabulary or containment check; nothing was guessed."), oneliner), status_code=502)
    return HTMLResponse(render_html(result["card"], oneliner))


def _withheld(note: str) -> dict[str, Any]:
    return {"presentation": None, "chief_complaint": "", "sections": {}, "blocked": {"removed": [], "violations": [], "note": note}}


@app.get("/record/{record_id}")
def get_record(record_id: str) -> JSONResponse:
    """Audit link: the verified record behind a card item. 404 unless the record is verified."""
    record = store.get_record(record_id, _db_path())
    if record is None or record.get("tier") not in config.RENDER_TIERS:
        raise HTTPException(status_code=404, detail="no verified record with that id")
    return JSONResponse(record)


@app.get("/health")
def health() -> dict[str, Any]:
    llm = app.state.llm
    return {"status": "ok", "model": getattr(llm, "model", None), "provider": config.LLM_PROVIDER, "records": _record_counts()}
