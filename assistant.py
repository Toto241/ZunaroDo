"""
Der KI-Assistent.

Er kennt KEIN einziges Fachmodul direkt. Er kennt nur die Registry
und damit die Schnittstelle. Dadurch funktioniert er mit jedem Modul,
das ModuleInterface erfuellt.

Zwei Betriebsarten:
  1) API-Modus  - echtes LLM (Anthropic), nutzt Tool-Use.
                  Aktiv, wenn die Umgebungsvariable ANTHROPIC_API_KEY
                  gesetzt ist und das Paket 'anthropic' installiert ist.
  2) Offline-Modus - regelbasierter Router. Braucht kein Netz, keine
                  Schluessel. Demonstriert dieselbe Schnittstelle.

Beide Modi rufen Faehigkeiten ausschliesslich ueber registry.dispatch()
auf - die Schnittstelle bleibt identisch.
"""
from __future__ import annotations

import json
import os

from core.interface import ModuleRegistry

SYSTEM_PROMPT = (
    "Du bist der Alltagshelfer, ein freundlicher deutschsprachiger "
    "Assistent. Du hilfst beim Verwalten von Vertraegen, Fristen und "
    "Finanzen. Nutze die bereitgestellten Werkzeuge, um echte Daten "
    "abzurufen, statt zu raten. Antworte knapp und konkret auf Deutsch."
)


class Assistant:
    """Orchestriert Nutzeranfragen ueber die Modul-Schnittstelle."""

    def __init__(self, registry: ModuleRegistry, model: str = "claude-opus-4-20250514"):
        self.registry = registry
        self.model = model
        self._client = self._try_init_client()

    # ------------------------------------------------------------------
    @staticmethod
    def _try_init_client():
        """Versucht den Anthropic-Client zu laden - sonst None (Offline)."""
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return None
        try:
            import anthropic
            return anthropic.Anthropic()
        except Exception:
            return None

    @property
    def mode(self) -> str:
        return "API" if self._client else "Offline"

    # ------------------------------------------------------------------
    def ask(self, user_message: str) -> str:
        """Eine Nutzeranfrage beantworten."""
        if self._client:
            return self._ask_api(user_message)
        return self._ask_offline(user_message)

    # ---- API-Modus -----------------------------------------------------
    def _ask_api(self, user_message: str) -> str:
        """Echte LLM-Schleife mit Tool-Use ueber die Schnittstelle."""
        tools = self.registry.tool_schemas()
        agenda = self.registry.collect_events()
        agenda_txt = "\n".join(
            f"- {e.due_date}: {e.title} (in {e.days_remaining} Tagen)"
            for e in agenda) or "keine"
        system = (SYSTEM_PROMPT
                  + "\n\nAktueller Stand:\n" + self.registry.context_overview()
                  + "\n\nAnstehende Ereignisse:\n" + agenda_txt)
        messages = [{"role": "user", "content": user_message}]

        # Schleife: solange das Modell Werkzeuge aufruft, weiter
        for _ in range(8):  # Sicherheitslimit gegen Endlosschleifen
            response = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                tools=tools,
                messages=messages,
            )
            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content
                               if b.type == "text")

            # Tool-Aufrufe ausfuehren - ueber die Registry-Schnittstelle
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                result = self.registry.dispatch(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            messages.append({"role": "user", "content": tool_results})

        return "Abbruch: zu viele Werkzeugaufrufe."

    # ---- Offline-Modus -------------------------------------------------
    def _ask_offline(self, user_message: str) -> str:
        """
        Regelbasierter Router. Er bildet die LLM-Logik nach: erkennt
        eine Absicht, ruft die passende Capability ueber dieselbe
        Schnittstelle (registry.dispatch) auf und formuliert die Antwort.
        """
        msg = user_message.lower()

        # Absicht: Kuendigungsschreiben erstellen (Modul A)
        if any(w in msg for w in ("kündigungsschreiben", "kuendigungsschreiben",
                                  "kündigung schreiben", "schreiben erstell")):
            return ("Ein Kuendigungsschreiben erstelle ich ueber "
                    "'contracts.generate_cancellation'. Nenne mir den Vertrag "
                    "(im API-Modus waehle ich ihn automatisch), dann erzeuge "
                    "ich PDF und Mail-Entwurf.")

        # Absicht: anstehende Fristen (Modul A)
        if any(w in msg for w in ("frist", "kuend", "künd", "auslauf", "ablauf")):
            within = 30 if any(w in msg for w in
                               ("monat", "30", "bald", "demn", "nächst", "naechst")) else None
            args = {"within_days": within} if within else {}
            data = self.registry.dispatch("contracts.upcoming_deadlines", args)
            return self._format_deadlines(data)

        # Absicht: Dashboard / anstehende Ereignisse (modul-uebergreifend)
        if any(w in msg for w in ("agenda", "dashboard", "ereignis",
                                  "was steht", "was kommt", "ueberblick",
                                  "überblick", "anstehend")):
            events = self.registry.collect_events()
            return self._format_agenda(events)

        # Absicht: Posteingang / Vorschlaege pruefen
        if any(w in msg for w in ("vorschlag", "vorschläge", "vorschlaege",
                                  "posteingang", "offene mail")):
            data = self.registry.dispatch("inbox.proposals", {})
            return self._format_proposals(data)

        # Absicht: Auftraege (einmalig) - Modul D
        if any(w in msg for w in ("auftrag", "aufträge", "auftraege")):
            data = self.registry.dispatch("family.orders", {})
            return self._format_orders(data)

        # Absicht: Familie / Haushalt / wiederkehrende Aufgaben (Modul D)
        if any(w in msg for w in ("familie", "haushalt", "aufgabe", "putzplan",
                                  "wer ist dran", "mitglied", "zustaendig",
                                  "zuständig", "chore")):
            data = self.registry.dispatch("family.tasks", {})
            return self._format_family_tasks(data)

        # Absicht: Finanzen / Budget / monatliche Belastung (Modul B)
        if any(w in msg for w in ("finanz", "budget", "belast", "monatlich", "ausgab")):
            if any(w in msg for w in ("liste", "auflist", "einzeln")):
                data = self.registry.dispatch("finance.list_expenses", {})
                return self._format_expense_list(data)
            data = self.registry.dispatch("finance.monthly_overview", {})
            return self._format_finance(data)

        # Absicht: Vertragsuebersicht (Modul A)
        if any(w in msg for w in ("vertrag", "übersicht", "uebersicht", "kosten")):
            data = self.registry.dispatch("contracts.list", {})
            return self._format_contracts(data)

        # Absicht: Preisaenderung melden
        if "preis" in msg:
            return ("Bitte nenne mir Vertrag und neuen Preis - im API-Modus "
                    "loese ich das automatisch ueber 'contracts.report_price_change'.")

        # Fallback: zeige, was der Assistent ueberhaupt kann
        caps = ", ".join(c.name for c in self.registry.all_capabilities())
        return ("Das habe ich nicht verstanden. Ueber die Schnittstelle "
                f"verfuegbar sind:\n  {caps}\n"
                "Frag mich z.B. nach 'anstehenden Fristen', einer "
                "'Vertragsuebersicht' oder deiner 'monatlichen Belastung'.")

    # ---- Antworten huebsch formatieren --------------------------------
    @staticmethod
    def _format_contracts(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es sind noch keine Vertraege erfasst."
        lines = [f"Du hast {data['count']} aktive Vertraege "
                 f"({data['total_monthly_cost']:.2f} EUR/Monat):"]
        for c in data["contracts"]:
            lines.append(f"  - {c['name']} ({c['provider']}): "
                         f"{c['monthly_cost']:.2f} EUR/Monat")
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
            f"({data['contract_count']} Vertraege, Quelle: {data['contract_costs_source']})\n"
            f"  - Einmalige Ausgaben diesen Monat: {data['one_time_this_month']:.2f} EUR "
            f"({data['expense_count']} Posten)\n"
            f"  => Gesamt: {data['total_monthly']:.2f} EUR"
        )

    @staticmethod
    def _format_expense_list(data: dict) -> str:
        if data.get("count", 0) == 0:
            return "Es sind noch keine Ausgaben erfasst."
        lines = [f"Erfasste Ausgaben ({data['total']:.2f} EUR gesamt):"]
        for e in data["expenses"]:
            lines.append(f"  - {e['spent_on']}  {e['description']}: "
                          f"{e['amount']:.2f} EUR [{e['category']}]")
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
