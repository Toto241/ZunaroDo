"""
Modul E - Soziale Pflege.

Erinnert daran, sich bei wichtigen Menschen zu melden. Jeder Kontakt
hat einen Wunsch-Rhythmus ('cadence_days'); wer laenger nicht
kontaktiert wurde, taucht im Dashboard als ueberfaellig auf.

Der Assistent kann zusaetzlich Vorschlaege fuer Nachrichten formulieren
(im API-Modus). Im Offline-Modus liefert das Modul einfache Vorlagen.
"""
from __future__ import annotations

from datetime import date, timedelta

from core.interface import Capability, ModuleContext, ModuleInterface
from database import SocialRepository
from models import Event, SocialContact


# Kleine Vorlagen-Bibliothek fuer Offline-Modus
_MESSAGE_TEMPLATES = {
    "kurz": "Hallo {name}, ich habe gerade an dich gedacht - wie geht es dir?",
    "treffen": ("Hallo {name}, ist eine Weile her - hast du Lust, dass wir "
                "uns demnaechst sehen?"),
    "geburtstag": ("Hallo {name}, alles Gute zum Geburtstag! Ich wuensche "
                   "dir ein tolles neues Jahr."),
}


class SocialModule(ModuleInterface):
    """Modul E als steckbares Fachmodul."""

    def __init__(self, repo: SocialRepository):
        self.repo = repo
        self._ctx: ModuleContext | None = None

    @property
    def module_id(self) -> str:
        return "social"

    @property
    def display_name(self) -> str:
        return "Soziale Pflege"

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def get_context_summary(self) -> str:
        kontakte = self.repo.list_all()
        if not kontakte:
            return "Noch keine Kontakte erfasst."
        ueberfaellig = sum(1 for c in kontakte
                           if self._days_remaining(c) < 0)
        return (f"{len(kontakte)} Kontakte erfasst, "
                f"{ueberfaellig} ueberfaellig.")

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        result: list[Event] = []
        for c in self.repo.list_all():
            days = self._days_remaining(c)
            due_date = self._next_due(c)
            if days > horizon_days:
                continue
            relation = f" ({c.relation})" if c.relation else ""
            result.append(Event(
                title=f"Melden bei {c.name}{relation}",
                due_date=due_date,
                module_id=self.module_id,
                module_name=self.display_name,
                category="sozial",
                detail=(c.notes
                        or f"Gewuenschter Rhythmus: alle {c.cadence_days} Tage."),
                days_remaining=days,
            ))
        return result

    # ---- Faehigkeiten --------------------------------------------------
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="social.add_contact",
                description="Legt einen Kontakt fuer die soziale Pflege an.",
                parameters={
                    "name": {"type": "string", "_required": True,
                             "description": "Name der Person"},
                    "relation": {"type": "string",
                                 "description": "Beziehung, z.B. Familie, "
                                                "Freund, Kollege"},
                    "cadence_days": {"type": "integer",
                                     "description": "Wunsch-Rhythmus in Tagen "
                                                    "(Standard: 30)"},
                    "notes": {"type": "string", "description": "Notizen"},
                },
                handler=self._cap_add,
            ),
            Capability(
                name="social.contacts",
                description="Listet alle Kontakte mit Resttagen bis zum "
                            "naechsten Melden auf.",
                parameters={},
                handler=self._cap_list,
            ),
            Capability(
                name="social.mark_contacted",
                description="Markiert einen Kontakt als gerade kontaktiert "
                            "(setzt last_contacted = heute).",
                parameters={
                    "contact_id": {"type": "integer", "_required": True,
                                   "description": "ID des Kontakts"},
                },
                handler=self._cap_mark_contacted,
            ),
            Capability(
                name="social.draft_message",
                description="Schlaegt eine kurze Nachricht fuer einen Kontakt "
                            "vor (Offline-Vorlage; im API-Modus generiert das "
                            "LLM eine persoenlichere).",
                parameters={
                    "contact_id": {"type": "integer", "_required": True,
                                   "description": "ID des Kontakts"},
                    "template": {"type": "string",
                                 "description": "kurz, treffen, geburtstag"},
                },
                handler=self._cap_draft_message,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_add(self, name: str, relation: str = "",
                 cadence_days: int = 30, notes: str = "") -> dict:
        c = SocialContact(name=name, relation=relation,
                          cadence_days=cadence_days, notes=notes)
        saved = self.repo.add(c)
        return {"status": "angelegt", "contact": saved.to_dict()}

    def _cap_list(self) -> dict:
        contacts = self.repo.list_all()
        result = []
        for c in contacts:
            entry = c.to_dict()
            entry["days_until_due"] = self._days_remaining(c)
            entry["next_due"] = self._next_due(c).isoformat()
            result.append(entry)
        return {"count": len(result), "contacts": result}

    def _cap_mark_contacted(self, contact_id: int) -> dict:
        c = self.repo.get(contact_id)
        if c is None:
            return {"error": f"Kontakt {contact_id} nicht gefunden"}
        self.repo.mark_contacted(contact_id)
        return {"status": "kontaktiert", "name": c.name,
                "next_due_in_days": c.cadence_days}

    def _cap_draft_message(self, contact_id: int,
                           template: str = "kurz") -> dict:
        c = self.repo.get(contact_id)
        if c is None:
            return {"error": f"Kontakt {contact_id} nicht gefunden"}
        tpl = _MESSAGE_TEMPLATES.get(template, _MESSAGE_TEMPLATES["kurz"])
        return {"status": "Entwurf",
                "to": c.name,
                "message": tpl.format(name=c.name),
                "template": template}

    # ---- intern --------------------------------------------------------
    def _next_due(self, c: SocialContact) -> date:
        last = c.last_contacted or date.today() - timedelta(days=c.cadence_days)
        return last + timedelta(days=c.cadence_days)

    def _days_remaining(self, c: SocialContact) -> int:
        return (self._next_due(c) - date.today()).days
