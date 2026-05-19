"""
Provider-agnostische LLM-Schnittstelle.

Definiert den Vertrag, den jeder LLM-Client erfuellen muss, damit der
Assistent ihn ohne Aenderung nutzen kann. Aktuell gibt es eine
Implementierung fuer Google Gemini (services/gemini.py); spaeter sind
weitere problemlos ergaenzbar.

Die Schnittstelle ist bewusst klein:
  - ask_with_tools(...) fuehrt eine komplette Konversationsrunde durch,
    inklusive Funktionsaufrufen ueber den uebergebenen Dispatcher.
  - analyze_text(...) ist die unstrukturierte Variante (Mail-Analyse,
    Nachrichten-Entwurf u. a.).

Damit das LLM kontrollierbar bleibt, kennt jede Capability einen Flag
'destructive'. Ist er gesetzt, fragt der Assistent vor dem Aufruf nach.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol


@dataclass
class TokenUsage:
    """Aufgelaufene Token-Nutzung (Eingabe + Ausgabe)."""
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens

    def to_dict(self) -> dict:
        return {"input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens}


@dataclass
class ToolCall:
    """Vom Modell ausgeloster Funktionsaufruf."""
    name: str
    args: dict
    is_destructive: bool = False


@dataclass
class LLMAnswer:
    """Antwort des LLM nach einer kompletten Runde."""
    text: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    tool_calls_done: int = 0
    truncated: bool = False
    pending_confirmations: list[ToolCall] = field(default_factory=list)
    # Aktualisierte Konversationshistorie nach dieser Runde. Format ist
    # provider-spezifisch (z.B. eine Liste von genai.protos.Content).
    # Der Assistant uebernimmt sie unveraendert und reicht sie beim
    # naechsten Aufruf wieder ein.
    updated_history: list = field(default_factory=list)


# Dispatcher: bekommt einen Aufruf, fuehrt ihn aus, gibt Ergebnis zurueck
Dispatcher = Callable[[str, dict], dict]
# Confirm-Callback: fragt Nutzer vor destruktivem Aufruf; Standard erlaubt
ConfirmCallback = Callable[[ToolCall], bool]


class LLMClient(Protocol):
    """Provider-agnostische Schnittstelle. Implementierungen liefern den Stand."""

    name: str
    model: str

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
    ) -> LLMAnswer: ...

    def analyze_text(
        self,
        instructions: str,
        text: str,
        max_output_tokens: int = 1024,
    ) -> tuple[str, TokenUsage]: ...
