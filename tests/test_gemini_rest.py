"""Desktop-Tests fuer den SDK-freien Gemini-REST-Client.

Die HTTP-Schicht wird vollstaendig gemockt - es geht hier nur um das
Request-/Response-Mapping und den Funktionsaufruf-Zyklus, nicht um echte
Netzwerk-Calls.
"""
from __future__ import annotations

import copy
import json

import pytest

from services.gemini_rest import GeminiRestClient
from services.llm_factory import build_gemini_client


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self) -> dict:
        return self._payload


class _FakeSession:
    """Liefert vorab definierte Antworten und merkt sich die Payloads."""

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.requests: list[dict] = []

    def post(self, url, json=None, timeout=None):   # noqa: A002 - API-Form
        # Snapshot der Payload festhalten - der Client mutiert die
        # contents-Liste danach weiter (echtes requests serialisiert sofort).
        self.requests.append({"url": url, "json": copy.deepcopy(json)})
        return _FakeResponse(self._responses.pop(0))


def test_disabled_without_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = GeminiRestClient(api_key=None)
    assert client.is_available is False


def test_plain_text_answer():
    session = _FakeSession([{
        "candidates": [{"content": {"parts": [{"text": "Hallo Welt"}]}}],
        "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3},
    }])
    client = GeminiRestClient(api_key="secret", session=session)
    answer = client.ask_with_tools(
        user_message="Hi",
        system_prompt_static="System",
        system_prompt_dynamic="",
        tool_specs=[],
        destructive_tool_names=set(),
        dispatcher=lambda name, args: {},
    )
    assert answer.text == "Hallo Welt"
    assert answer.usage.input_tokens == 5
    assert answer.usage.output_tokens == 3
    assert answer.tool_calls_done == 0
    # Key steckt in der URL, nicht in der Payload.
    assert "key=secret" in session.requests[0]["url"]
    assert session.requests[0]["json"]["system_instruction"][
        "parts"][0]["text"] == "System"


def test_function_call_roundtrip():
    # Runde 1: Modell ruft ein Werkzeug auf. Runde 2: liefert finalen Text.
    session = _FakeSession([
        {"candidates": [{"content": {"parts": [
            {"functionCall": {"name": "finance_list",
                              "args": {"month": "06"}}}]}}],
         "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 4}},
        {"candidates": [{"content": {"parts": [
            {"text": "Du hast 3 Ausgaben."}]}}],
         "usageMetadata": {"promptTokenCount": 8, "candidatesTokenCount": 6}},
    ])
    seen = {}

    def dispatcher(name, args):
        seen["name"] = name
        seen["args"] = args
        return {"count": 3}

    client = GeminiRestClient(api_key="secret", session=session)
    answer = client.ask_with_tools(
        user_message="Wie viele Ausgaben?",
        system_prompt_static="System",
        system_prompt_dynamic="Heute ist Montag",
        tool_specs=[{"name": "finance.list",
                     "description": "Listet Ausgaben",
                     "parameters": {"type": "object"}}],
        destructive_tool_names=set(),
        dispatcher=dispatcher,
    )
    assert answer.text == "Du hast 3 Ausgaben."
    assert answer.tool_calls_done == 1
    # Punkt-Namen werden Gemini-sicher gemappt und zurueckuebersetzt.
    assert seen["name"] == "finance.list"
    assert seen["args"] == {"month": "06"}
    # Token beider Runden summiert.
    assert answer.usage.input_tokens == 18
    assert answer.usage.output_tokens == 10
    # Zweite Anfrage enthaelt die functionResponse in der Historie.
    second_payload = session.requests[1]["json"]
    roles = [c["role"] for c in second_payload["contents"]]
    assert roles == ["user", "model", "user"]


def test_destructive_call_skipped_without_confirm():
    session = _FakeSession([
        {"candidates": [{"content": {"parts": [
            {"functionCall": {"name": "finance_delete", "args": {"id": 1}}}]}}]},
        {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]},
    ])
    client = GeminiRestClient(api_key="secret", session=session)
    answer = client.ask_with_tools(
        user_message="Loesche Ausgabe 1",
        system_prompt_static="S",
        system_prompt_dynamic="",
        tool_specs=[{"name": "finance.delete", "description": "x",
                     "parameters": {"type": "object"}}],
        destructive_tool_names={"finance.delete"},
        dispatcher=lambda name, args: {"deleted": True},
        confirm=lambda call: False,   # Nutzer lehnt ab
    )
    assert answer.pending_confirmations
    assert answer.pending_confirmations[0].name == "finance.delete"
    assert answer.tool_calls_done == 0


def test_http_error_raises_without_leaking_key():
    class _ErrSession:
        def post(self, url, json=None, timeout=None):   # noqa: A002
            return _FakeResponse({"error": "boom"}, status_code=403)

    client = GeminiRestClient(api_key="topsecret", session=_ErrSession())
    with pytest.raises(RuntimeError) as exc:
        client.analyze_text("inst", "text")
    assert "topsecret" not in str(exc.value)


def test_factory_picks_rest_when_forced(monkeypatch):
    monkeypatch.setenv("ALLTAGSHELFER_FORCE_GEMINI_REST", "1")
    client = build_gemini_client(api_key="k")
    assert client.name == "gemini-rest"
