"""
Notes-Modul: freie Notizen, optional an eine Entitaet (Vertrag, Termin,
Kontakt, Familienmitglied, Ausgabe) angeheftet.

Sechs Capabilities:
  - notes.add(title, content, entity_type=?, entity_id=?)
  - notes.list(entity_type=?, entity_id=?)
  - notes.get(note_id)
  - notes.update(note_id, title=?, content=?)
  - notes.attach(note_id, entity_type=?, entity_id=?)
  - notes.delete(note_id)
"""
from __future__ import annotations

from core.interface import Capability, ModuleInterface
from database import NoteRepository
from models import Note


_VALID_ENTITY_TYPES = {
    "contracts", "expenses", "calendar", "social", "family", "orders"}


class NotesModule(ModuleInterface):

    def __init__(self, repo: NoteRepository):
        self.repo = repo

    @property
    def module_id(self) -> str:
        return "notes"

    @property
    def display_name(self) -> str:
        return "Notizen"

    def get_context_summary(self) -> str:
        notes = self.repo.list_all()
        if not notes:
            return "Noch keine Notizen erfasst."
        attached = sum(1 for n in notes if n.entity_type)
        return (f"{len(notes)} Notiz(en), davon {attached} an Entitaeten "
                f"geheftet.")

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="notes.add",
                description="Legt eine neue Notiz an. Optional an eine "
                            "Entitaet angeheftet (entity_type, entity_id).",
                parameters={
                    "title": {"type": "string", "_required": True,
                              "description": "Titel der Notiz"},
                    "content": {"type": "string",
                                 "description": "Notiz-Text"},
                    "entity_type": {"type": "string",
                                      "description": "Optional: contracts, "
                                                     "expenses, calendar, "
                                                     "social, family, orders"},
                    "entity_id": {"type": "integer",
                                    "description": "Optional: ID innerhalb "
                                                   "der Entitaet"},
                },
                handler=self._cap_add,
            ),
            Capability(
                name="notes.list",
                description="Listet Notizen auf. Optional nach Entitaet "
                            "gefiltert.",
                parameters={
                    "entity_type": {"type": "string",
                                      "description": "Filter auf Entitaet"},
                    "entity_id": {"type": "integer",
                                    "description": "Filter auf konkrete ID"},
                },
                handler=self._cap_list,
            ),
            Capability(
                name="notes.get",
                description="Liefert eine konkrete Notiz.",
                parameters={
                    "note_id": {"type": "integer", "_required": True,
                                 "description": "ID der Notiz"},
                },
                handler=self._cap_get,
            ),
            Capability(
                name="notes.update",
                description="Aktualisiert Titel und/oder Inhalt einer Notiz.",
                parameters={
                    "note_id": {"type": "integer", "_required": True,
                                 "description": "ID der Notiz"},
                    "title": {"type": "string",
                               "description": "Neuer Titel (optional)"},
                    "content": {"type": "string",
                                 "description": "Neuer Inhalt (optional)"},
                },
                handler=self._cap_update,
                destructive=True,
            ),
            Capability(
                name="notes.attach",
                description="Heftet eine Notiz an eine Entitaet (oder "
                            "loest sie mit entity_type=null).",
                parameters={
                    "note_id": {"type": "integer", "_required": True,
                                 "description": "ID der Notiz"},
                    "entity_type": {"type": "string",
                                      "description": "Entitaets-Typ "
                                                     "(leer = nichts anheften)"},
                    "entity_id": {"type": "integer",
                                    "description": "ID der Entitaet"},
                },
                handler=self._cap_attach,
                destructive=True,
            ),
            Capability(
                name="notes.delete",
                description="Loescht eine Notiz endgueltig.",
                parameters={
                    "note_id": {"type": "integer", "_required": True,
                                 "description": "ID der Notiz"},
                },
                handler=self._cap_delete,
                destructive=True,
            ),
            Capability(
                name="notes.cleanup_for_entity",
                description="Loescht alle Notizen, die an die angegebene "
                            "Entitaet geheftet sind. Wird intern von den "
                            "Loesch-Capabilities anderer Module aufgerufen.",
                parameters={
                    "entity_type": {"type": "string", "_required": True,
                                      "description": "Entitaets-Typ"},
                    "entity_id": {"type": "integer", "_required": True,
                                    "description": "ID der Entitaet"},
                },
                handler=self._cap_cleanup_for_entity,
                destructive=True,
                internal=True,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_add(self, title: str, content: str = "",
                  entity_type: str | None = None,
                  entity_id: int | None = None) -> dict:
        title = (title or "").strip()
        if not title:
            return {"error": "title darf nicht leer sein"}
        if entity_type and entity_type not in _VALID_ENTITY_TYPES:
            return {"error": f"entity_type '{entity_type}' nicht erlaubt; "
                              f"gueltig: {sorted(_VALID_ENTITY_TYPES)}"}
        # Wichtig: 'is None' statt 'if entity_id' - sonst wuerden gueltige
        # IDs wie 0 still zu None (H4).
        eid = entity_id if entity_id is not None else None
        note = Note(title=title, content=content,
                     entity_type=entity_type or None,
                     entity_id=eid)
        saved = self.repo.add(note)
        return {"status": "angelegt", "note": saved.to_dict()}

    def _cap_list(self, entity_type: str | None = None,
                    entity_id: int | None = None) -> dict:
        if entity_type:
            notes = self.repo.list_attached(entity_type, entity_id)
        else:
            notes = self.repo.list_all()
        return {"count": len(notes),
                "notes": [n.to_dict() for n in notes]}

    def _cap_get(self, note_id: int) -> dict:
        note = self.repo.get(note_id)
        if note is None:
            return {"error": f"Notiz {note_id} nicht gefunden"}
        return {"note": note.to_dict()}

    def _cap_update(self, note_id: int,
                     title: str | None = None,
                     content: str | None = None) -> dict:
        updated = self.repo.update(note_id, title=title, content=content)
        if updated is None:
            return {"error": f"Notiz {note_id} nicht gefunden"}
        return {"status": "aktualisiert", "note": updated.to_dict()}

    def _cap_attach(self, note_id: int,
                     entity_type: str | None = None,
                     entity_id: int | None = None) -> dict:
        if entity_type and entity_type not in _VALID_ENTITY_TYPES:
            return {"error": f"entity_type '{entity_type}' nicht erlaubt"}
        eid = entity_id if entity_id is not None else None
        updated = self.repo.attach(note_id, entity_type or None, eid)
        if updated is None:
            return {"error": f"Notiz {note_id} nicht gefunden"}
        return {"status": "verknuepft", "note": updated.to_dict()}

    def _cap_delete(self, note_id: int) -> dict:
        if not self.repo.delete(note_id):
            return {"error": f"Notiz {note_id} nicht gefunden"}
        return {"status": "geloescht", "note_id": note_id}

    def _cap_cleanup_for_entity(self, entity_type: str,
                                  entity_id: int) -> dict:
        removed = self.repo.delete_for_entity(entity_type, entity_id)
        return {"status": "aufgeraeumt", "removed": removed}
