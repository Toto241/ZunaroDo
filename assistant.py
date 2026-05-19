"""
Der KI-Assistent (Provider-agnostisch, Default: Google Gemini).

Er kennt KEIN einziges Fachmodul direkt. Er kennt nur die Registry
und einen LLMClient. Dadurch funktioniert er mit jedem Modul, das
ModuleInterface erfuellt, und mit jedem Provider, der die kleine
LLMClient-Schnittstelle umsetzt.

Drei Betriebsarten:
  1) Gemini (API)  - echtes LLM mit Funktionsaufrufen
                     Aktiv, wenn GOOGLE_API_KEY/GEMINI_API_KEY gesetzt
                     ist und 'google-generativeai' installiert.
  2) Offline       - regelbasierter Router (auch ohne Netz/Key nutzbar)

Erweiterungen gegenueber der frueheren Anthropic-Anbindung:
  - Konversationsverlauf pro Session
  - konfigurierbare Iterations- und Token-Limits
  - Token-Verbrauch wird protokolliert
  - destruktive Capabilities erfordern einen ConfirmCallback
  - stabiler Teil des System-Prompts ist von der dynamischen Lage getrennt
  - LLM-Antwort und Tool-Aufrufe landen im assistant_log
"""
from __future__ import annotations

import json
import threading
from typing import Callable, Optional

from core.interface import ModuleRegistry
from database import AssistantLogRepository
from services.gemini import GeminiClient
from services.llm import ConfirmCallback, LLMAnswer, LLMClient, TokenUsage


SYSTEM_PROMPT_STATIC = (
    "Du bist der Alltagshelfer, ein freundlicher deutschsprachiger "
    "Assistent. Du hilfst beim Verwalten von Vertraegen, Fristen, "
    "Finanzen, Haushalt, Terminen und Kontakten. Nutze konsequent die "
    "bereitgestellten Werkzeuge, um echte Daten abzurufen, statt zu "
    "raten. Bei Werkzeugen mit dauerhaften Aenderungen (z.B. Daten "
    "aendern oder Aktionen ausloesen) bestaetige sicherheitshalber kurz, "
    "was du gleich tust. Antworte knapp und konkret auf Deutsch."
)


def _allow_all(_call) -> bool:
    """Default-Confirm: erlaubt alles. GUI/CLI ueberschreibt das."""
    return True


class Assistant:
    """Orchestriert Nutzeranfragen ueber die Modul-Schnittstelle."""

    def __init__(self, registry: ModuleRegistry,
                 llm: Optional[LLMClient] = None,
                 log: Optional[AssistantLogRepository] = None,
                 max_iterations: int = 12,
                 max_output_tokens: int = 2048):
        self.registry = registry
        self.log = log
        self.max_iterations = max_iterations
        self.max_output_tokens = max_output_tokens

        # Provider-Wahl: explizit uebergeben > Gemini-Default > Offline
        if llm is not None:
            self.llm: Optional[LLMClient] = llm
        else:
            candidate = GeminiClient()
            self.llm = candidate if candidate.is_available else None

        # Konversationsverlauf pro Session (Liste von genai.Content-Objekten
        # oder Dictionaries; Provider-spezifisch). Der LLMClient ist
        # zustaendig, das passende Format zu interpretieren.
        self._history: list = []
        # Aufgelaufener Token-Verbrauch
        self._usage = TokenUsage()
        # Confirm-Callback fuer destruktive Aufrufe
        self._confirm: ConfirmCallback = _allow_all
        # Lock fuer 'ask' - verhindert, dass zwei GUI-Sends parallel
        # in _history/_usage schreiben (H7).
        self._ask_lock = threading.Lock()

    # ------------------------------------------------------------------
    @property
    def mode(self) -> str:
        if self.llm is None:
            return "Offline"
        return f"API ({self.llm.name})"

    @property
    def token_usage(self) -> TokenUsage:
        return self._usage

    def set_confirm_callback(self,
                              callback: Optional[ConfirmCallback]) -> None:
        """Vor destruktiven Aufrufen wird dieser Callback gefragt."""
        self._confirm = callback if callback is not None else _allow_all

    def reset_history(self) -> None:
        self._history = []

    # ------------------------------------------------------------------
    def ask(self, user_message: str,
            stream_callback: Optional[Callable[[str], None]] = None) -> str:
        # Serialisieren: zwei parallele asks haetten sonst auf _history
        # und _usage Race-Conditions (H7).
        with self._ask_lock:
            if self.log is not None:
                self.log.append("user", user_message)
            if self.llm is None:
                answer = self._ask_offline(user_message)
            else:
                answer = self._ask_api(user_message, stream_callback)
            if self.log is not None:
                self.log.append("assistant", answer)
            return answer

    # ---- API-Modus -----------------------------------------------------
    def _ask_api(self, user_message: str,
                  stream_callback: Optional[Callable[[str], None]]) -> str:
        assert self.llm is not None    # in ask() bereits geprueft
        agenda = self.registry.collect_events()
        agenda_txt = "\n".join(
            f"- {e.due_date}: {e.title} (in {e.days_remaining} Tagen, "
            f"{e.module_name})"
            for e in agenda[:20]) or "keine"
        dynamic = ("Aktueller Stand:\n"
                    + self.registry.context_overview()
                    + "\n\nAnstehende Ereignisse:\n" + agenda_txt)

        try:
            result: LLMAnswer = self.llm.ask_with_tools(
                user_message=user_message,
                system_prompt_static=SYSTEM_PROMPT_STATIC,
                system_prompt_dynamic=dynamic,
                tool_specs=self.registry.tool_schemas(),
                destructive_tool_names=self.registry.destructive_capability_names(),
                dispatcher=lambda name, args: self.registry.dispatch(name, args),
                history=self._history,
                max_iterations=self.max_iterations,
                max_output_tokens=self.max_output_tokens,
                confirm=self._confirm,
                stream_callback=stream_callback,
            )
        except Exception as exc:                            # noqa: BLE001
            # Netz, Rate-Limit, Schema-Fehler etc. - wir lassen die GUI
            # nicht haengen, sondern liefern eine klare Meldung.
            return (f"Der KI-Aufruf an Gemini ist fehlgeschlagen: {exc}. "
                    "Versuch es erneut oder schalte zurueck in den "
                    "Offline-Modus, indem du GOOGLE_API_KEY entfernst.")
        # Konversationsverlauf fortschreiben - so kann das Modell beim
        # naechsten Aufruf auf den bisherigen Dialog zurueckgreifen.
        if result.updated_history:
            self._history = result.updated_history
        self._usage.add(result.usage)
        if self.log is not None:
            self.log.append(
                "meta",
                json.dumps({"tokens": result.usage.to_dict(),
                             "tool_calls": result.tool_calls_done,
                             "truncated": result.truncated}))
        return result.text

    # ---- Offline-Modus -------------------------------------------------
    def _ask_offline(self, user_message: str) -> str:
        msg = user_message.lower()

        if any(w in msg for w in ("kündigungsschreiben", "kuendigungsschreiben",
                                  "kündigung schreiben", "schreiben erstell")):
            return ("Ein Kuendigungsschreiben erstelle ich ueber "
                    "'contracts.generate_cancellation'. Im API-Modus waehle ich "
                    "den Vertrag automatisch und erzeuge PDF + Mail-Entwurf.")

        if any(w in msg for w in ("frist", "kuend", "künd", "auslauf", "ablauf")):
            within = 30 if any(w in msg for w in
                               ("monat", "30", "bald", "demn", "nächst",
                                "naechst")) else None
            args = {"within_days": within} if within else {}
            return self._format_deadlines(
                self.registry.dispatch("contracts.upcoming_deadlines", args))

        if any(w in msg for w in ("einkauf", "einkaufsliste", "einkaufen",
                                  "supermarkt")):
            return self._format_shopping(
                self.registry.dispatch("family.shopping_list", {}))

        if any(w in msg for w in ("kontakt", "melden", "freund", "anrufen",
                                  "anruf", "kümmer", "kuemmer")):
            return self._format_social(
                self.registry.dispatch("social.contacts", {}))

        if any(w in msg for w in ("termin", "kalender", "garantie", "tuev",
                                  "tüv", "steuer", "geburtstag")):
            return self._format_calendar(self.registry.dispatch(
                "calendar.upcoming", {"horizon_days": 90}))

        if any(w in msg for w in ("agenda", "dashboard", "ereignis",
                                  "was steht", "was kommt", "ueberblick",
                                  "überblick", "anstehend")):
            return self._format_agenda(self.registry.collect_events())

        if any(w in msg for w in ("vorschlag", "vorschläge", "vorschlaege",
                                  "posteingang", "offene mail")):
            return self._format_proposals(
                self.registry.dispatch("inbox.proposals", {}))

        if any(w in msg for w in ("auftrag", "aufträge", "auftraege")):
            return self._format_orders(
                self.registry.dispatch("family.orders", {}))

        if any(w in msg for w in ("familie", "haushalt", "aufgabe", "putzplan",
                                  "wer ist dran", "mitglied", "zustaendig",
                                  "zuständig", "chore")):
            return self._format_family_tasks(
                self.registry.dispatch("family.tasks", {}))

        if any(w in msg for w in ("finanz", "budget", "belast", "monatlich",
                                  "ausgab")):
            if any(w in msg for w in ("liste", "auflist", "einzeln")):
                return self._format_expense_list(
                    self.registry.dispatch("finance.list_expenses", {}))
            return self._format_finance(
                self.registry.dispatch("finance.monthly_overview", {}))

        if "preisgedächtnis" in msg or "preis gedächtnis" in msg or \
           "preisgedaechtnis" in msg:
            return self._format_price_memory(
                self.registry.dispatch("finance.price_memory", {}))

        if any(w in msg for w in ("vertrag", "übersicht", "uebersicht",
                                  "kosten")):
            return self._format_contracts(
                self.registry.dispatch("contracts.list", {}))

        if "preis" in msg:
            return ("Bitte nenne mir Vertrag und neuen Preis - im API-Modus "
                    "loese ich das automatisch ueber "
                    "'contracts.report_price_change'.")

        caps = ", ".join(c.name for c in self.registry.all_capabilities())
        return ("Das habe ich nicht verstanden. Ueber die Schnittstelle "
                f"verfuegbar sind:\n  {caps}\n"
                "Frag mich z.B. nach 'anstehenden Fristen', einer "
                "'Vertragsuebersicht' oder deiner 'monatlichen Belastung'.")

    # ---- Formatter -----------------------------------------------------
    @staticmethod
    def _format_contracts(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es sind noch keine Vertraege erfasst."
        lines = [f"Du hast {data['count']} aktive Vertraege "
                 f"({data['total_monthly_cost']:.2f} EUR/Monat):"]
        for c in data["contracts"]:
            owner = f" - {c['owner']}" if c.get("owner") else ""
            lines.append(f"  - {c['name']} ({c.get('provider') or '-'}): "
                         f"{c['monthly_cost']:.2f} EUR/Monat{owner}")
        return "\n".join(lines)

    @staticmethod
    def _format_deadlines(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Aktuell stehen keine Kuendigungsfristen an."
        lines = ["Anstehende Kuendigungsfristen:"]
        for d in data["deadlines"]:
            days = d["days_remaining"]
            mark = "  !!! " if days <= 30 else "  - "
            lines.append(f"{mark}{d['contract_name']}: bis {d['due_date']} "
                         f"({days} Tage)")
        return "\n".join(lines)

    @staticmethod
    def _format_finance(data: dict) -> str:
        return (
            f"Monatliche Belastung fuer {data['month']}:\n"
            f"  - Wiederkehrende Vertraege: {data['recurring_contracts']:.2f} EUR "
            f"({data['contract_count']} Vertraege, Quelle: "
            f"{data['contract_costs_source']})\n"
            f"  - Einmalige Ausgaben diesen Monat: "
            f"{data['one_time_this_month']:.2f} EUR "
            f"({data['expense_count']} Posten)\n"
            f"  => Gesamt: {data['total_monthly']:.2f} EUR"
        )

    @staticmethod
    def _format_expense_list(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es sind noch keine Ausgaben erfasst."
        lines = [f"Erfasste Ausgaben ({data['total']:.2f} EUR gesamt):"]
        for e in data["expenses"]:
            owner = f"  -  {e['owner']}" if e.get("owner") else ""
            lines.append(f"  - {e['spent_on']}  {e['description']}: "
                          f"{e['amount']:.2f} EUR [{e['category']}]{owner}")
        return "\n".join(lines)

    @staticmethod
    def _format_agenda(events: list) -> str:
        if not events:
            return "Aktuell stehen keine Ereignisse an."
        mark = {"hoch": "!!!", "mittel": " ! ", "normal": "  -"}
        lines = ["Deine naechsten Ereignisse:"]
        for e in events:
            d = e.days_remaining
            when = (f"in {d} Tagen" if d > 0
                    else "heute faellig" if d == 0
                    else f"{-d} Tage ueberfaellig")
            lines.append(f" {mark[e.urgency]} {e.due_date}  {e.title}  "
                          f"({when}, {e.module_name})")
        return "\n".join(lines)

    @staticmethod
    def _format_family_tasks(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es sind noch keine Haushaltsaufgaben erfasst."
        lines = ["Haushaltsaufgaben:"]
        for t in data["tasks"]:
            lines.append(f"  - {t['title']}: faellig {t['next_due']}, "
                          f"zustaendig {t['current_assignee']} "
                          f"(alle {t['interval_days']} Tage)")
        return "\n".join(lines)

    @staticmethod
    def _format_orders(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es sind keine Auftraege erfasst."
        lines = ["Auftraege:"]
        for o in data["orders"]:
            status = "[erledigt]" if o["status"] == "erledigt" else "[offen]"
            faellig = f", faellig {o['due_date']}" if o["due_date"] else ""
            lines.append(f"  {status} {o['title']} -> "
                          f"{o['assignee'] or 'niemand'}{faellig}")
        return "\n".join(lines)

    @staticmethod
    def _format_proposals(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es liegen keine offenen Vorschlaege vor."
        lines = ["Offene Vorschlaege (warten auf Pruefung):"]
        for p in data["proposals"]:
            lines.append(f"  #{p['id']}  {p['summary']}")
            lines.append(f"        Ziel: {p['target_capability']}")
        lines.append("Uebernehmen mit 'inbox.accept_proposal', "
                      "ablehnen mit 'inbox.reject_proposal'.")
        return "\n".join(lines)

    @staticmethod
    def _format_calendar(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Keine Termine im Horizont."
        lines = [f"Termine in den naechsten {data.get('horizon_days', 90)} Tagen:"]
        for e in data["events"]:
            extra = f" ({e['person']})" if e.get("person") else ""
            lines.append(f"  - {e['due_date']}  {e['title']}{extra} "
                          f"[{e['category']}]")
        return "\n".join(lines)

    @staticmethod
    def _format_social(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Keine Kontakte fuer die soziale Pflege erfasst."
        lines = ["Wichtige Kontakte:"]
        for c in data["contacts"]:
            days = c.get("days_until_due", 0)
            when = (f"in {days} Tagen" if days > 0
                    else "heute faellig" if days == 0
                    else f"{-days} Tage ueberfaellig")
            lines.append(f"  - {c['name']} ({c.get('relation') or 'Kontakt'}): "
                          f"{when}, naechstes Mal {c['next_due']}")
        return "\n".join(lines)

    @staticmethod
    def _format_shopping(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Die Einkaufsliste ist leer."
        lines = ["Einkaufsliste:"]
        for item in data["items"]:
            mark = "[x]" if item.get("bought") else "[ ]"
            qty = f" ({item['quantity']})" if item.get("quantity") else ""
            by = f" (von {item['added_by']})" if item.get("added_by") else ""
            lines.append(f"  {mark} {item['name']}{qty}{by}")
        return "\n".join(lines)

    @staticmethod
    def _format_price_memory(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Noch keine gemerkten Preise."
        lines = ["Preisgedaechtnis:"]
        for p in data["products"]:
            seen = f" (zuletzt {p['last_seen']})" if p.get("last_seen") else ""
            lines.append(f"  - {p['product']}: {p['last_price']:.2f} EUR{seen}")
        return "\n".join(lines)
