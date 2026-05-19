"""
Google-Gemini-Client fuer den Alltagshelfer.

Implementiert die Schnittstelle aus services/llm.py mit dem
'google-generativeai'-Paket. Aktiv, sobald GOOGLE_API_KEY oder
GEMINI_API_KEY gesetzt ist UND das Paket installiert ist.

Erweiterungen, die aus der Anthropic-Analyse abgeleitet wurden:
  - Konversationsverlauf wird durchgereicht
  - Konfigurierbare Iterations- und Token-Limits
  - Token-Verbrauch wird gemessen
  - Trennung stabiler / dynamischer System-Prompt (Gemini Context Cache
    spaeter problemlos einsetzbar)
  - Provider-agnostisches Capability-Schema (Capability erzeugt zwei
    Varianten - Anthropic-Stil und Gemini-Stil)
  - 'destructive'-Flag pro Capability: vor dem Ausfuehren fragt der
    Assistent ueber den ConfirmCallback nach
  - Tool-Fehler werden strukturiert zurueckgegeben, nicht als Plain-Text
"""
from __future__ import annotations

import json
import os
from typing import Callable, Optional

from services.llm import (ConfirmCallback, Dispatcher, LLMAnswer, ToolCall,
                          TokenUsage)


# Gemini-Funktionsnamen muessen Identifier sein - Punkte ersetzen
def _gemini_safe(name: str) -> str:
    return name.replace(".", "_").replace("-", "_")


def _resolve_api_key() -> Optional[str]:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


def _try_import():
    """Versucht 'google-generativeai' zu laden."""
    try:
        import google.generativeai as genai
        return genai
    except Exception:
        return None


class GeminiClient:
    """Konkrete LLM-Anbindung an Google Gemini."""

    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self._genai = _try_import()
        api_key = _resolve_api_key()
        self._enabled = bool(self._genai and api_key)
        if self._enabled:
            self._genai.configure(api_key=api_key)

    @property
    def is_available(self) -> bool:
        return self._enabled

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
            raise RuntimeError("Gemini nicht verfuegbar (Key fehlt oder "
                                "'google-generativeai' nicht installiert)")
        genai = self._genai

        # ---- Tools ins Gemini-Schema bringen --------------------------
        # Punkte aus Capability-Namen entfernen, Mapping merken
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
        tools = [{"function_declarations": function_declarations}]

        # ---- System-Prompt (statisch + dynamisch) ---------------------
        system_instruction = system_prompt_static
        if system_prompt_dynamic:
            system_instruction += "\n\n---\n" + system_prompt_dynamic

        model = genai.GenerativeModel(
            self.model,
            tools=tools,
            system_instruction=system_instruction,
        )
        chat = model.start_chat(history=history or [])

        usage = TokenUsage()
        tool_calls_done = 0
        pending_confirmations: list[ToolCall] = []

        message_for_next_turn: object = user_message
        for _ in range(max_iterations):
            response = chat.send_message(
                message_for_next_turn,
                generation_config={"max_output_tokens": max_output_tokens},
            )
            usage.add(self._extract_usage(response))

            function_calls: list = []
            text_parts: list[str] = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, "function_call") and part.function_call.name:
                    function_calls.append(part.function_call)
                elif hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if stream_callback and text_parts:
                stream_callback("".join(text_parts))

            if not function_calls:
                # Modell ist fertig
                return LLMAnswer(
                    text="".join(text_parts).strip()
                          or "(kein Inhalt - Modell hat geschwiegen)",
                    usage=usage,
                    tool_calls_done=tool_calls_done,
                    truncated=False,
                    pending_confirmations=pending_confirmations,
                )

            # ---- Tool-Aufrufe ausfuehren ------------------------------
            tool_responses = []
            for call in function_calls:
                original_name = name_map.get(call.name, call.name)
                args = dict(call.args) if call.args else {}
                tc = ToolCall(name=original_name, args=args,
                               is_destructive=original_name in destructive_tool_names)
                if tc.is_destructive and confirm is not None and not confirm(tc):
                    pending_confirmations.append(tc)
                    result = {"status": "uebersprungen",
                              "hinweis": ("Destruktiver Aufruf vom Nutzer "
                                          "nicht bestaetigt.")}
                else:
                    try:
                        result = dispatcher(original_name, args)
                    except Exception as exc:                    # noqa: BLE001
                        result = {"error": f"Ausnahme: {exc}"}
                    tool_calls_done += 1
                tool_responses.append(genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=call.name,
                        response={"result": result},
                    )))
            message_for_next_turn = genai.protos.Content(
                role="user", parts=tool_responses)

        return LLMAnswer(
            text=("(Abbruch: maximale Tool-Iterationen erreicht. "
                   "Bitte konkreter nachfragen.)"),
            usage=usage,
            tool_calls_done=tool_calls_done,
            truncated=True,
            pending_confirmations=pending_confirmations,
        )

    # ------------------------------------------------------------------
    def analyze_text(self, instructions: str, text: str,
                      max_output_tokens: int = 1024) -> tuple[str, TokenUsage]:
        if not self._enabled:
            raise RuntimeError("Gemini nicht verfuegbar")
        model = self._genai.GenerativeModel(self.model)
        response = model.generate_content(
            [instructions, text],
            generation_config={"max_output_tokens": max_output_tokens},
        )
        usage = self._extract_usage(response)
        text_out = getattr(response, "text", "") or ""
        return text_out.strip(), usage

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_usage(response) -> TokenUsage:
        meta = getattr(response, "usage_metadata", None)
        if meta is None:
            return TokenUsage()
        return TokenUsage(
            input_tokens=int(getattr(meta, "prompt_token_count", 0) or 0),
            output_tokens=int(getattr(meta, "candidates_token_count", 0) or 0),
        )
