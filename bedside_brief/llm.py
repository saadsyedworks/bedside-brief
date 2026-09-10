"""Single thin LLM client. The only module in the package that talks to a provider.

Contract: `complete_json(system, user, schema) -> dict`. Strict JSON-schema output is
requested first; if the provider rejects strict mode the call is retried with plain
JSON mode and the reply is validated locally against the same schema. Every reply is
validated locally regardless, so callers can trust the shape.

Never logged: the API key, the Authorization header, prompt text, or reply text.
Logged: model name, token usage, latency.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable

import jsonschema

import config

log = logging.getLogger("bedside_brief.llm")

_PING_MESSAGES = [{"role": "user", "content": "ping"}]


class LLMError(RuntimeError):
    """Provider or contract failure (bad JSON, schema mismatch, unsupported provider)."""


class LLMClient:
    """OpenAI chat-completions client. Same temperature/seed for parser, ranker and arm C."""

    def __init__(self, provider: str = config.LLM_PROVIDER, model: str = config.LLM_MODEL) -> None:
        if provider != "openai":
            raise LLMError(f"unsupported LLM_PROVIDER {provider!r}; only 'openai' is implemented")
        self.provider = provider
        self.model = model
        self.temperature = config.LLM_TEMPERATURE
        self.seed = config.LLM_SEED
        self._client: Any = None

    # --- provider ---------------------------------------------------------------------
    def _sdk(self) -> Any:
        """Lazy SDK construction so importing this module never needs a key or network."""
        if self._client is None:
            from openai import OpenAI  # local import: tests never touch the SDK

            self._client = OpenAI(api_key=config.openai_api_key())  # key is read, never logged
        return self._client

    def startup_check(self) -> str:
        """One-token call. On a 404 for the primary model fall back to LLM_FALLBACK_MODEL.
        Returns (and stores) the resolved model name."""
        from openai import NotFoundError

        for model in (self.model, config.LLM_FALLBACK_MODEL):
            try:
                t0 = time.perf_counter()
                self._sdk().chat.completions.create(model=model, messages=_PING_MESSAGES, max_completion_tokens=1)
                log.info("startup_check ok model=%s latency_ms=%d", model, (time.perf_counter() - t0) * 1000)
                self.model = model
                return model
            except NotFoundError:
                log.warning("startup_check: model %s not found", model)
        raise LLMError("neither primary nor fallback model is available")

    # --- completion -------------------------------------------------------------------
    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        from openai import BadRequestError

        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        strict = {
            "type": "json_schema",
            "json_schema": {"name": schema.get("title", "reply"), "schema": schema, "strict": True},
        }
        try:
            raw = self._call(messages, strict)
        except BadRequestError as exc:
            log.warning("strict json_schema rejected (%s); retrying with json_object + local validation", type(exc).__name__)
            raw = self._call(messages, {"type": "json_object"})
        return _parse_and_validate(raw, schema)

    def _call(self, messages: list[dict[str, str]], response_format: dict[str, Any]) -> str:
        t0 = time.perf_counter()
        resp = None
        for attempt in range(6):  # 429 / transient 5xx: exponential backoff, deterministic request otherwise
            try:
                resp = self._sdk().chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format=response_format,
                    temperature=self.temperature,
                    seed=self.seed,
                )
                break
            except Exception as exc:  # noqa: BLE001
                name = type(exc).__name__
                status = getattr(exc, "status_code", None)
                retryable = name in ("RateLimitError", "APITimeoutError", "APIConnectionError", "InternalServerError") or status in (429, 500, 502, 503, 504)
                if not retryable or attempt == 5:
                    raise
                wait = min(30.0, 1.5 * (2 ** attempt))
                log.warning("%s on attempt %d; sleeping %.1fs", name, attempt + 1, wait)
                time.sleep(wait)
        usage = getattr(resp, "usage", None)
        log.info(
            "complete model=%s prompt_tokens=%s completion_tokens=%s latency_ms=%d",
            self.model,
            getattr(usage, "prompt_tokens", "?"),
            getattr(usage, "completion_tokens", "?"),
            (time.perf_counter() - t0) * 1000,
        )
        content = resp.choices[0].message.content
        if not content:
            raise LLMError("empty completion")
        return content


def _parse_and_validate(raw: str, schema: dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise LLMError(f"reply is not valid JSON: {exc}") from exc
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        raise LLMError(f"reply violates schema at {'/'.join(map(str, exc.path)) or '<root>'}: {exc.message[:120]}") from exc
    return data


class FakeLLM:
    """Offline stand-in. Returns canned dicts in order (a single dict is returned every time,
    a callable is invoked with (system, user, schema)). Records every prompt in `.calls`."""

    def __init__(self, responses: dict[str, Any] | list[dict[str, Any]] | Callable[..., dict[str, Any]], model: str = "fake-model") -> None:
        self._responses = responses
        self._queue = list(responses) if isinstance(responses, list) else None
        self.model = model
        self.calls: list[dict[str, Any]] = []

    def startup_check(self) -> str:
        return self.model

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"system": system, "user": user, "schema": schema})
        if callable(self._responses):
            reply = self._responses(system, user, schema)
        elif self._queue is not None:
            if not self._queue:
                raise LLMError("FakeLLM: no canned responses left")
            reply = self._queue.pop(0)
        else:
            reply = self._responses
        return _parse_and_validate(json.dumps(reply), schema)
