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

    def __init__(self, repo: SocialRepository, llm=None):
        self.repo = repo
        self.llm = llm
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
                name="social.import_vcard",
                description="Liest eine vCard-Datei (.vcf) und legt die "
                            "enthaltenen Kontakte an. Bestehende Kontakte "
                            "bleiben unveraendert - es entstehen neue "
                            "Eintraege.",
                parameters={
                    "path": {"type": "string", "_required": True,
                             "description": "Pfad zur .vcf-Datei"},
                },
                handler=self._cap_import_vcard,
                destructive=True,
                internal=True,
            ),
            Capability(
                name="social.export_vcard",
                description="Exportiert alle Kontakte als vCard-Datei (.vcf), "
                            "importierbar in jedes gaengige Adressbuch.",
                parameters={
                    "path": {"type": "string", "_required": True,
                             "description": "Zielpfad (sollte auf .vcf enden)"},
                },
                handler=self._cap_export_vcard,
            ),
            Capability(
                name="social.delete_contact",
                description="Loescht einen Kontakt endgueltig.",
                parameters={
                    "contact_id": {"type": "integer", "_required": True,
                                   "description": "ID des Kontakts"},
                },
                handler=self._cap_delete,
                destructive=True,
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
                    "anlass": {"type": "string",
                                "description": "Optional: konkreter Anlass, "
                                               "den das LLM aufgreifen soll"},
                },
                handler=self._cap_draft_message,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_add(self, name: str, relation: str = "",
                 cadence_days: int = 30, notes: str = "") -> dict:
        if not name or not name.strip():
            return {"error": "Name darf nicht leer sein"}
        if cadence_days <= 0:
            return {"error": "cadence_days muss positiv sein"}
        c = SocialContact(name=name.strip(), relation=relation,
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

    def _cap_delete(self, contact_id: int) -> dict:
        existed = self.repo.delete(contact_id)
        if not existed:
            return {"error": f"Kontakt {contact_id} nicht gefunden"}
        if (self._ctx is not None
                and self._ctx.has_capability("notes.cleanup_for_entity")):
            self._ctx.call("notes.cleanup_for_entity",
                            entity_type="social", entity_id=contact_id)
        return {"status": "geloescht", "contact_id": contact_id}

    def _cap_export_vcard(self, path: str) -> dict:
        from pathlib import Path
        from services.vcard import export_contacts
        target = Path(path)
        count = export_contacts(self.repo.list_all(), target)
        return {"status": "exportiert", "count": count, "path": str(target)}

    def _cap_import_vcard(self, path: str) -> dict:
        from services.io_validation import validate_import_path
        from services.vcard import import_contacts
        try:
            safe_path = validate_import_path(
                path, allowed_extensions={".vcf"})
            contacts = import_contacts(safe_path)
        except (FileNotFoundError, ValueError) as exc:
            return {"error": str(exc)}
        accepted = 0
        rejected: list[str] = []
        # Durch _cap_add laufen - so greift die Pflichtfeld- und
        # cadence_days-Validierung.
        for c in contacts:
            result = self._cap_add(
                name=c.name, relation=c.relation,
                cadence_days=c.cadence_days, notes=c.notes)
            if result.get("status") == "angelegt":
                accepted += 1
            else:
                rejected.append(result.get("error", str(result)))
        return {"status": "importiert", "count": accepted,
                "rejected": rejected[:5], "rejected_total": len(rejected),
                "path": str(safe_path)}

    def _cap_mark_contacted(self, contact_id: int) -> dict:
        c = self.repo.get(contact_id)
        if c is None:
            return {"error": f"Kontakt {contact_id} nicht gefunden"}
        self.repo.mark_contacted(contact_id)
        return {"status": "kontaktiert", "name": c.name,
                "next_due_in_days": c.cadence_days}

    def _cap_draft_message(self, contact_id: int,
                           template: str = "kurz",
                           anlass: str = "") -> dict:
        c = self.repo.get(contact_id)
        if c is None:
            return {"error": f"Kontakt {contact_id} nicht gefunden"}
        # Wenn ein LLM verfuegbar ist, einen persoenlicheren Entwurf bauen
        if self.llm is not None and getattr(self.llm, "is_available", False):
            try:
                message = self._draft_with_llm(c, template, anlass)
                if message:
                    return {"status": "Entwurf (LLM)",
                            "to": c.name,
                            "message": message,
                            "template": template}
            except Exception:                              # pragma: no cover
                pass
        tpl = _MESSAGE_TEMPLATES.get(template, _MESSAGE_TEMPLATES["kurz"])
        return {"status": "Entwurf",
                "to": c.name,
                "message": tpl.format(name=c.name),
                "template": template}

    def _draft_with_llm(self, contact: SocialContact, template: str,
                         anlass: str) -> str:
        instruction = (
            "Du formulierst eine kurze, herzliche, persoenliche Nachricht "
            "auf Deutsch (1-3 Saetze). Schreibe direkt im Du, ohne Anrede "
            "wie 'Hallo,'. Keine Emojis, kein Marketing-Ton. Liefer nur den "
            "Text der Nachricht, keine zusaetzliche Erklaerung. Vorlage-"
            f"Charakter: '{template}'. Empfaenger: {contact.name}, "
            f"Beziehung: {contact.relation or 'persoenlich'}. "
            f"Anlass: {anlass or 'einfach mal melden'}.")
        text, _ = self.llm.analyze_text(instruction, "")
        return text.strip()

    # ---- intern --------------------------------------------------------
    def _next_due(self, c: SocialContact) -> date:
        last = c.last_contacted or date.today() - timedelta(days=c.cadence_days)
        return last + timedelta(days=c.cadence_days)

    def _days_remaining(self, c: SocialContact) -> int:
        return (self._next_due(c) - date.today()).days
