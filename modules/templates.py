"""
Vorlagen fuer wiederkehrende Haushaltsaufgaben (Modul D-Erweiterung).

Statt jede Woche „Muell rausbringen" mit allen Feldern neu zu tippen,
kann der Nutzer Vorlagen anlegen und sie dann ueber 'family.add_task'
schnell instanzieren. Vorlagen sind reine Templates (Titel + Intervall
+ Beschreibung) - die Zuweisungs-Rotation kommt erst beim Anwenden.
"""
from __future__ import annotations

from core.interface import Capability, ModuleContext, ModuleInterface
from database import TaskTemplateRepository
from models import TaskTemplate


class TaskTemplatesModule(ModuleInterface):

    def __init__(self, repo: TaskTemplateRepository):
        self.repo = repo
        self._ctx: ModuleContext | None = None

    @property
    def module_id(self) -> str:
        return "templates"

    @property
    def display_name(self) -> str:
        return "Aufgaben-Vorlagen"

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def get_context_summary(self) -> str:
        items = self.repo.list_all()
        return f"{len(items)} Vorlage(n)."

    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="templates.add",
                description="Legt eine neue Aufgaben-Vorlage an.",
                parameters={
                    "title": {"type": "string", "_required": True,
                              "description": "Titel der Aufgabe"},
                    "interval_days": {"type": "integer",
                                        "description": "Tages-Intervall "
                                                       "(Standard 7)"},
                    "description": {"type": "string",
                                      "description": "Notiz zur Vorlage"},
                },
                handler=self._cap_add,
            ),
            Capability(
                name="templates.list",
                description="Listet alle vorhandenen Aufgaben-Vorlagen auf.",
                parameters={},
                handler=self._cap_list,
            ),
            Capability(
                name="templates.delete",
                description="Loescht eine Vorlage endgueltig.",
                parameters={
                    "template_id": {"type": "integer", "_required": True,
                                      "description": "ID der Vorlage"},
                },
                handler=self._cap_delete,
                destructive=True,
            ),
            Capability(
                name="templates.apply",
                description="Erzeugt aus einer Vorlage eine konkrete "
                            "Haushaltsaufgabe - die Rotation muss zusaetzlich "
                            "angegeben werden.",
                parameters={
                    "template_id": {"type": "integer", "_required": True,
                                      "description": "ID der Vorlage"},
                    "assignees": {"type": "array",
                                    "items": {"type": "string"},
                                    "_required": True,
                                    "description": "Namen der "
                                                   "Rotationsmitglieder"},
                    "first_due": {"type": "string",
                                    "description": "Erste Faelligkeit "
                                                   "(YYYY-MM-DD); Standard: "
                                                   "heute"},
                },
                handler=self._cap_apply,
                destructive=True,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_add(self, title: str, interval_days: int = 7,
                  description: str = "") -> dict:
        title = (title or "").strip()
        if not title:
            return {"error": "title darf nicht leer sein"}
        if interval_days <= 0:
            return {"error": "interval_days muss positiv sein"}
        saved = self.repo.add(TaskTemplate(
            title=title, interval_days=interval_days,
            description=description))
        return {"status": "angelegt", "template": saved.to_dict()}

    def _cap_list(self) -> dict:
        items = self.repo.list_all()
        return {"count": len(items),
                "templates": [t.to_dict() for t in items]}

    def _cap_delete(self, template_id: int) -> dict:
        if not self.repo.delete(template_id):
            return {"error": f"Vorlage {template_id} nicht gefunden"}
        return {"status": "geloescht", "template_id": template_id}

    def _cap_apply(self, template_id: int, assignees: list[str],
                    first_due: str | None = None) -> dict:
        tpl = self.repo.get(template_id)
        if tpl is None:
            return {"error": f"Vorlage {template_id} nicht gefunden"}
        if self._ctx is None or not self._ctx.has_capability(
                "family.add_task"):
            return {"error": "Modul D (Familie) nicht verfuegbar"}
        return self._ctx.call(
            "family.add_task",
            title=tpl.title, interval_days=tpl.interval_days,
            assignees=assignees, first_due=first_due)
