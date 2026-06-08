"""
REST-basierter Google-Gemini-Client (ohne 'google-generativeai'-SDK).

Warum diese Variante existiert:
  Das SDK 'google-generativeai' zieht grpcio + protobuf als
  C-Extensions nach. Auf Android (python-for-android / Buildozer) sind
  diese Pakete praktisch nicht baubar. Damit der KI-Assistent auch in
  der Mobile-App funktioniert, spricht dieser Client die Gemini-REST-API
  direkt ueber 'requests' an - und 'requests' ist im Buildozer-Build
  ohnehin vorhanden.

Der Client implementiert exakt dieselbe Schnittstelle wie
services/gemini.py (services.llm.LLMClient), inklusive Funktionsaufrufen
('function calling'), destruktiver Bestaetigung und Token-Messung. Der
Assistent kann ihn deshalb ohne jede Aenderung verwenden; die Auswahl
SDK vs. REST trifft services/llm_factory.py.

Konversationshistorie: Format ist hier eine reine Liste von JSON-Dicts
('contents' im REST-Schema). Sie ist - anders als die genai.protos-
Objekte des SDK - direkt serialisierbar.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Optional

import requests

from services.llm import (ConfirmCallback, Dispatcher, LLMAnswer, ToolCall,
                          TokenUsage)

# Basis-Endpunkt der Gemini-REST-API. Der Key wird als ?key=... angehaengt
# (so dokumentiert Google die generativelanguage-API); niemals in Logs.
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
_TIMEOUT = 60


# Gemini-Funktionsnamen muessen Identifier sein - Punkte/Striche ersetzen.
# Identisch zu services/gemini.py, damit beide Clients gleich abbilden.
def _gemini_safe(name: str) -> str:
    return name.replace(".", "_").replace("-", "_")


def _resolve_api_key() -> Optional[str]:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


class GeminiRestClient:
    """LLM-Anbindung an Gemini ueber die REST-API (SDK-frei)."""

    name = "gemini-rest"

    def __init__(self, model: str = "gemini-2.5-flash",
                 api_key: Optional[str] = None,
                 session: Optional[requests.Session] = None):
        self.model = model
        self._api_key = api_key or _resolve_api_key() or ""
        self._enabled = bool(self._api_key)
        self._session = session or requests.Session()

    @property
    def is_available(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    def _endpoint(self, method: str) -> str:
        return f"{_API_BASE}/models/{self.model}:{method}?key={self._api_key}"

    def _post(self, method: str, payload: dict) -> dict:
        resp = self._session.post(self._endpoint(method), json=payload,
                                  timeout=_TIMEOUT)
        if resp.status_code >= 400:
            # Fehlertext OHNE den Key (steckt nur in der URL) weiterreichen.
            raise RuntimeError(
                f"Gemini-REST-Fehler {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    # ------------------------------------------------------------------
    @staticmethod
    def _usage_from(response: dict) -> TokenUsage:
        meta = response.get("usageMetadata") or {}
        return TokenUsage(
            input_tokens=int(meta.get("promptTokenCount", 0) or 0),
            output_tokens=int(meta.get("candidatesTokenCount", 0) or 0),
        )

    @staticmethod
    def _parts_of(response: dict) -> list[dict]:
        candidates = response.get("candidates") or []
        if not candidates:
            return []
        content = candidates[0].get("content") or {}
        return content.get("parts") or []

    # ------------------------------------------------------------------
    def ask_with_tools(
        self,
        user_message: str,
        system_prompt_static: str,
        system_prompt_dynamic: str,
        tool_specs: list[dict],
        destructive_tool_names: set[str],
        dispatcher: Dispatcher,
        history: Optional[list] = None,
        max_iterations: int = 12,
        max_output_tokens: int = 2048,
        confirm: Optional[ConfirmCallback] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> LLMAnswer:
        if not self._enabled:
            raise RuntimeError("Gemini nicht verfuegbar (Key fehlt)")

        # ---- Tools ins Gemini-Schema bringen --------------------------
        name_map: dict[str, str] = {}
        function_declarations: list[dict] = []
        for spec in tool_specs:
            original = spec["name"]
            safe = _gemini_safe(original)
            name_map[safe] = original
            function_declarations.append({
                "name": safe,
                "description": spec["description"],
                "parameters": spec["parameters"],
            })
        tools = [{"function_declarations": function_declarations}] \
            if function_declarations else []

        # ---- System-Prompt (statisch + dynamisch) ---------------------
        system_instruction = system_prompt_static
        if system_prompt_dynamic:
            system_instruction += "\n\n---\n" + system_prompt_dynamic

        # contents = bisherige Historie + neue Nutzer-Nachricht
        contents: list[dict] = list(history or [])
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        usage = TokenUsage()
        tool_calls_done = 0
        pending_confirmations: list[ToolCall] = []

        for _ in range(max_iterations):
            payload: dict[str, Any] = {
                "contents": contents,
                "generationConfig": {"maxOutputTokens": max_output_tokens},
            }
            if system_instruction:
                payload["system_instruction"] = {
                    "parts": [{"text": system_instruction}]}
            if tools:
                payload["tools"] = tools

            response = self._post("generateContent", payload)
            usage.add(self._usage_from(response))
            parts = self._parts_of(response)

            text_parts: list[str] = []
            function_calls: list[dict] = []
            for part in parts:
                if "functionCall" in part and part["functionCall"].get("name"):
                    function_calls.append(part["functionCall"])
                elif part.get("text"):
                    text_parts.append(part["text"])

            # Antwort des Modells in die Historie aufnehmen.
            contents.append({"role": "model", "parts": parts})

            if not function_calls:
                full_text = "".join(text_parts).strip()
                if stream_callback is not None and full_text:
                    # REST hier ohne echtes Streaming - Text einmalig liefern.
                    stream_callback(full_text)
                return LLMAnswer(
                    text=full_text or "(kein Inhalt - Modell hat geschwiegen)",
                    usage=usage,
                    tool_calls_done=tool_calls_done,
                    truncated=False,
                    pending_confirmations=pending_confirmations,
                    updated_history=contents,
                )

            # ---- Tool-Aufrufe ausfuehren ------------------------------
            tool_response_parts: list[dict] = []
            for call in function_calls:
                safe_name = call.get("name", "")
                original_name = name_map.get(safe_name, safe_name)
                args = dict(call.get("args") or {})
                tc = ToolCall(
                    name=original_name, args=args,
                    is_destructive=original_name in destructive_tool_names)
                if tc.is_destructive and confirm is not None and not confirm(tc):
                    pending_confirmations.append(tc)
                    result: Any = {
                        "status": "uebersprungen",
                        "hinweis": ("Destruktiver Aufruf vom Nutzer nicht "
                                    "bestaetigt.")}
                else:
                    try:
                        result = dispatcher(original_name, args)
                    except Exception as exc:                    # noqa: BLE001
                        result = {"error": f"Ausnahme: {exc}"}
                    tool_calls_done += 1
                tool_response_parts.append({
                    "functionResponse": {
                        "name": safe_name,
                        "response": {"result": result},
                    }})
            contents.append({"role": "user", "parts": tool_response_parts})

        return LLMAnswer(
            text=("(Abbruch: maximale Tool-Iterationen erreicht. "
                  "Bitte konkreter nachfragen.)"),
            usage=usage,
            tool_calls_done=tool_calls_done,
            truncated=True,
            pending_confirmations=pending_confirmations,
            updated_history=contents,
        )

    # ------------------------------------------------------------------
    def analyze_text(self, instructions: str, text: str,
                     max_output_tokens: int = 1024) -> tuple[str, TokenUsage]:
        if not self._enabled:
            raise RuntimeError("Gemini nicht verfuegbar")
        payload = {
            "contents": [{"role": "user", "parts": [
                {"text": instructions}, {"text": text}]}],
            "generationConfig": {"maxOutputTokens": max_output_tokens},
        }
        response = self._post("generateContent", payload)
        usage = self._usage_from(response)
        text_out = "".join(
            part.get("text", "") for part in self._parts_of(response))
        return text_out.strip(), usage
