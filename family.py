"""
Modul D - Familie & Haushalt.

Scharf abgegrenzter Zweck: Haushaltsorganisation - wer ist wofuer
zustaendig. NICHT enthalten: allgemeine Erinnerungen (-> Termine-Modul),
Geld (-> Modul B).

Zwei Rollen im Gesamtsystem:
  1. Eigene Funktion: wiederkehrende Haushaltsaufgaben mit Rotation.
     Faellige Aufgaben liefert es ueber get_events() ans Dashboard.
  2. Querschnitts-Dimension: die Capability 'family.members' stellt die
     Haushaltsmitglieder bereit. Andere Module koennen sie ueber den
     ModuleContext abrufen, um ihre Eintraege einer Person zuzuordnen
     (z.B. ein Vertrag oder eine Ausgabe "gehoert" einer Person).
"""
from __future__ import annotations

from datetime import date, timedelta

from core.interface import Capability, ModuleContext, ModuleInterface
from database import FamilyRepository
from models import Event, FamilyMember, HouseholdOrder, HouseholdTask


class FamilyModule(ModuleInterface):
    """Modul D als steckbares Fachmodul."""

    def __init__(self, repo: FamilyRepository):
        self.repo = repo
        self._ctx: ModuleContext | None = None

    # ---- Pflichtangaben des Interface ---------------------------------
    @property
    def module_id(self) -> str:
        return "family"

    @property
    def display_name(self) -> str:
        return "Familie & Haushalt"

    def on_register(self, context: ModuleContext) -> None:
        self._ctx = context

    def get_context_summary(self) -> str:
        members = self.repo.list_members()
        tasks = self.repo.list_tasks()
        orders = self.repo.list_orders(only_open=True)
        if not members:
            return "Es sind noch keine Haushaltsmitglieder erfasst."
        today = date.today()
        due = sum(1 for t in tasks
                  if t.next_due and (t.next_due - today).days <= 0)
        text = (f"{len(members)} Haushaltsmitglieder, "
                f"{len(tasks)} wiederkehrende Aufgaben, "
                f"{len(orders)} offene Auftraege.")
        if due:
            text += f" {due} Aufgabe(n) heute oder ueberfaellig!"
        return text

    def get_events(self, horizon_days: int = 90) -> list[Event]:
        """Faellige Aufgaben UND offene Auftraege werden Dashboard-Ereignisse."""
        today = date.today()
        events: list[Event] = []

        # wiederkehrende Haushaltsaufgaben (mit Rotation)
        for t in self.repo.list_tasks():
            if t.next_due is None:
                continue
            days = (t.next_due - today).days
            if days > horizon_days:
                continue                    # ueberfaellige (negativ) bleiben drin
            assignee = t.current_assignee_name or "niemand zugeordnet"
            events.append(Event(
                title=f"Haushaltsaufgabe: {t.title}",
                due_date=t.next_due,
                module_id=self.module_id,
                module_name=self.display_name,
                category="aufgabe",
                detail=f"Diese Runde zustaendig: {assignee}.",
                days_remaining=days,
            ))

        # einmalige Auftraege (gezielt zugewiesen, nur offene)
        for o in self.repo.list_orders(only_open=True):
            if o.due_date is None:
                continue
            days = (o.due_date - today).days
            if days > horizon_days:
                continue
            detail = f"Zugewiesen an {o.assignee_name or 'niemanden'}."
            if o.description:
                detail += f" {o.description}"
            events.append(Event(
                title=f"Auftrag: {o.title}",
                due_date=o.due_date,
                module_id=self.module_id,
                module_name=self.display_name,
                category="auftrag",
                detail=detail,
                days_remaining=days,
            ))
        return events

    # ---- Faehigkeiten --------------------------------------------------
    def get_capabilities(self) -> list[Capability]:
        return [
            Capability(
                name="family.members",
                description="Listet die Haushaltsmitglieder auf. Auch von "
                            "anderen Modulen nutzbar, um Eintraege einer "
                            "Person zuzuordnen.",
                parameters={},
                handler=self._cap_members,
            ),
            Capability(
                name="family.add_member",
                description="Fuegt ein Haushaltsmitglied hinzu.",
                parameters={
                    "name": {"type": "string", "_required": True,
                             "description": "Name der Person"},
                    "role": {"type": "string",
                             "description": "erwachsen, kind oder sonstiges"},
                },
                handler=self._cap_add_member,
            ),
            Capability(
                name="family.add_task",
                description="Legt eine wiederkehrende Haushaltsaufgabe mit "
                            "Rotation zwischen Mitgliedern an.",
                parameters={
                    "title": {"type": "string", "_required": True,
                              "description": "Bezeichnung der Aufgabe"},
                    "interval_days": {"type": "integer",
                                      "description": "Wiederholung in Tagen "
                                                     "(z.B. 7 = woechentlich)"},
                    "assignees": {"type": "array", "items": {"type": "string"},
                                  "_required": True,
                                  "description": "Namen der Mitglieder in "
                                                 "Rotationsreihenfolge"},
                    "first_due": {"type": "string",
                                  "description": "Erste Faelligkeit ISO "
                                                 "(YYYY-MM-DD), Standard: heute"},
                },
                handler=self._cap_add_task,
            ),
            Capability(
                name="family.tasks",
                description="Listet die Haushaltsaufgaben mit aktueller "
                            "Zustaendigkeit und naechster Faelligkeit auf.",
                parameters={},
                handler=self._cap_tasks,
            ),
            Capability(
                name="family.complete_task",
                description="Hakt eine Aufgabe ab: die Rotation rueckt zur "
                            "naechsten Person, die Aufgabe wird neu terminiert.",
                parameters={
                    "task_id": {"type": "integer", "_required": True,
                                "description": "ID der Aufgabe"},
                },
                handler=self._cap_complete_task,
            ),
            Capability(
                name="family.add_order",
                description="Legt einen einmaligen Auftrag an, gezielt einer "
                            "Person zugewiesen (mit Termin).",
                parameters={
                    "title": {"type": "string", "_required": True,
                              "description": "Was ist zu erledigen"},
                    "assignee": {"type": "string",
                                 "description": "Name der zustaendigen Person"},
                    "due_date": {"type": "string",
                                 "description": "Faelligkeit ISO (YYYY-MM-DD)"},
                    "description": {"type": "string",
                                    "description": "Zusatzinfo zum Auftrag"},
                },
                handler=self._cap_add_order,
            ),
            Capability(
                name="family.orders",
                description="Listet die einmaligen Auftraege mit Zustaendigkeit "
                            "und Status auf.",
                parameters={},
                handler=self._cap_orders,
            ),
            Capability(
                name="family.complete_order",
                description="Markiert einen Auftrag als erledigt.",
                parameters={
                    "order_id": {"type": "integer", "_required": True,
                                 "description": "ID des Auftrags"},
                },
                handler=self._cap_complete_order,
            ),
        ]

    # ---- Handler -------------------------------------------------------
    def _cap_members(self) -> dict:
        members = self.repo.list_members()
        return {"count": len(members),
                "members": [m.to_dict() for m in members]}

    def _cap_add_member(self, name: str, role: str = "erwachsen") -> dict:
        saved = self.repo.add_member(FamilyMember(name=name, role=role))
        return {"status": "hinzugefuegt", "member": saved.to_dict()}

    def _cap_add_task(self, title: str, assignees: list[str],
                      interval_days: int = 7,
                      first_due: str | None = None) -> dict:
        # Namen in Mitglieder-IDs aufloesen
        rotation: list[int] = []
        unknown: list[str] = []
        for name in assignees:
            member = self.repo.find_member_by_name(name)
            if member and member.id is not None:
                rotation.append(member.id)
            else:
                unknown.append(name)
        if not rotation:
            return {"error": "Keine gueltigen Mitglieder fuer die Rotation",
                    "unknown": unknown}
        task = HouseholdTask(
            title=title,
            interval_days=interval_days,
            next_due=date.fromisoformat(first_due) if first_due else date.today(),
            rotation=rotation,
        )
        saved = self.repo.add_task(task)
        result = {"status": "angelegt", "task": self.repo.get_task(saved.id).to_dict()}
        if unknown:
            result["warnung"] = f"Unbekannte Namen ignoriert: {', '.join(unknown)}"
        return result

    def _cap_tasks(self) -> dict:
        tasks = self.repo.list_tasks()
        return {"count": len(tasks),
                "tasks": [t.to_dict() for t in tasks]}

    def _cap_complete_task(self, task_id: int) -> dict:
        try:
            task = self.repo.complete_task(task_id)
        except ValueError as exc:
            return {"error": str(exc)}
        return {"status": "abgehakt",
                "task": task.to_dict(),
                "next_assignee": task.current_assignee_name}

    def _cap_add_order(self, title: str, assignee: str = "",
                       due_date: str | None = None,
                       description: str = "") -> dict:
        assignee_id = None
        assignee_name = ""
        if assignee:
            member = self.repo.find_member_by_name(assignee)
            if member is None:
                return {"error": f"Mitglied '{assignee}' nicht gefunden"}
            assignee_id = member.id
            assignee_name = member.name
        order = HouseholdOrder(
            title=title,
            assignee_id=assignee_id,
            due_date=date.fromisoformat(due_date) if due_date else None,
            description=description,
        )
        saved = self.repo.add_order(order)
        saved.assignee_name = assignee_name
        return {"status": "Auftrag angelegt", "order": saved.to_dict()}

    def _cap_orders(self) -> dict:
        orders = self.repo.list_orders()
        return {"count": len(orders),
                "orders": [o.to_dict() for o in orders]}

    def _cap_complete_order(self, order_id: int) -> dict:
        order = self.repo.complete_order(order_id)
        if order is None:
            return {"error": f"Auftrag {order_id} nicht gefunden"}
        return {"status": "Auftrag erledigt", "order": order.to_dict()}
