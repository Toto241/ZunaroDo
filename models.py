"""
Domaenenmodelle des Alltagshelfers.

Reine Datenklassen ohne Logik - sie bilden die "Sprache",
in der Datenmodell, Module und KI-Assistent miteinander reden.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Contract:
    """Ein Vertrag (Versicherung, Mobilfunk, Streaming, Strom ...)."""
    name: str
    category: str                       # versicherung | mobilfunk | streaming | strom | sonstiges
    provider: str = ""
    customer_number: str = ""           # Kunden-/Vertragsnummer (fuer Kuendigung)
    start_date: Optional[date] = None
    minimum_term_months: int = 12       # Mindestlaufzeit
    notice_period_months: int = 3       # Kuendigungsfrist
    auto_renew_months: int = 12         # Verlaengerung bei Nicht-Kuendigung
    monthly_cost: float = 0.0
    currency: str = "EUR"
    notes: str = ""
    status: str = "active"              # active | cancelled | expired
    owner_id: Optional[int] = None      # Querschnitts-Person via family.members
    owner_name: str = ""                # nur Anzeige, nicht persistiert
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None    # Soft-Delete (Papierkorb)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "provider": self.provider,
            "customer_number": self.customer_number,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "minimum_term_months": self.minimum_term_months,
            "notice_period_months": self.notice_period_months,
            "auto_renew_months": self.auto_renew_months,
            "monthly_cost": self.monthly_cost,
            "currency": self.currency,
            "notes": self.notes,
            "status": self.status,
            "owner_id": self.owner_id,
            "owner": self.owner_name,
        }


@dataclass
class Expense:
    """Eine einmalige Ausgabe (Modul B - Finanzen)."""
    description: str
    amount: float
    category: str = "sonstiges"
    spent_on: Optional[date] = None
    owner_id: Optional[int] = None
    owner_name: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "spent_on": self.spent_on.isoformat() if self.spent_on else None,
            "owner_id": self.owner_id,
            "owner": self.owner_name,
        }


@dataclass
class Deadline:
    """In-memory: errechnete Frist zu einem Vertrag (wird nicht persistiert)."""
    contract_id: int
    type: str                           # cancellation | renewal | price_change
    due_date: date
    title: str
    resolved: bool = False
    id: Optional[int] = None
    contract_name: str = ""
    days_remaining: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "contract_name": self.contract_name,
            "type": self.type,
            "title": self.title,
            "due_date": self.due_date.isoformat(),
            "days_remaining": self.days_remaining,
            "resolved": self.resolved,
        }


def classify_urgency(days_remaining: int) -> str:
    """Leitet aus den verbleibenden Tagen eine Dringlichkeitsstufe ab."""
    if days_remaining <= 14:
        return "hoch"
    if days_remaining <= 30:
        return "mittel"
    return "normal"


@dataclass
class Event:
    """Ein anstehendes Ereignis fuer das Dashboard - modul-uebergreifend."""
    title: str
    due_date: date
    module_id: str
    module_name: str
    category: str = "erinnerung"
    detail: str = ""
    days_remaining: int = 0

    @property
    def urgency(self) -> str:
        return classify_urgency(self.days_remaining)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "due_date": self.due_date.isoformat(),
            "module_id": self.module_id,
            "module_name": self.module_name,
            "category": self.category,
            "detail": self.detail,
            "days_remaining": self.days_remaining,
            "urgency": self.urgency,
        }


@dataclass
class FamilyMember:
    """Ein Haushaltsmitglied (Modul D)."""
    name: str
    role: str = "erwachsen"
    birthday: Optional[date] = None      # fuer Geburtstags-Reminder
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "birthday": self.birthday.isoformat() if self.birthday else None,
        }


@dataclass
class HouseholdTask:
    """Wiederkehrende Haushaltsaufgabe mit Rotation (Modul D)."""
    title: str
    interval_days: int = 7
    next_due: Optional[date] = None
    rotation: list[int] = field(default_factory=list)
    current_index: int = 0
    id: Optional[int] = None
    current_assignee_name: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "interval_days": self.interval_days,
            "next_due": self.next_due.isoformat() if self.next_due else None,
            "current_assignee": self.current_assignee_name,
            "rotation_size": len(self.rotation),
        }


@dataclass
class HouseholdOrder:
    """Einmaliger Auftrag (Modul D) - gezielt zugewiesen."""
    title: str
    assignee_id: Optional[int] = None
    due_date: Optional[date] = None
    description: str = ""
    status: str = "offen"
    priority: str = "normal"            # hoch | mittel | normal
    category: str = ""
    id: Optional[int] = None
    assignee_name: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "assignee": self.assignee_name,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
        }


@dataclass
class ShoppingItem:
    """Eintrag auf der gemeinsamen Einkaufsliste (Modul D)."""
    name: str
    quantity: str = ""
    added_by_id: Optional[int] = None
    bought: bool = False
    id: Optional[int] = None
    added_by_name: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "quantity": self.quantity,
            "added_by": self.added_by_name,
            "bought": self.bought,
        }


@dataclass
class Proposal:
    """Vorschlag in der zentralen Vorschlags-Ablage."""
    source: str
    summary: str
    target_capability: str
    payload: dict = field(default_factory=dict)
    status: str = "offen"
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "summary": self.summary,
            "target_capability": self.target_capability,
            "payload": self.payload,
            "status": self.status,
        }


@dataclass
class CalendarEvent:
    """
    Ein Termin im Modul C (Termine & Kalender).

    Deckt: Behoerdentermine, Garantien, TUEV, Steuerfristen, allgemeine
    Erinnerungen, wiederkehrende Geburtstage (technisch gleich).
    """
    title: str
    due_date: date
    category: str = "termin"            # termin | garantie | tuev | steuer | geburtstag | sonstiges
    description: str = ""
    recurrence_days: Optional[int] = None    # z.B. 365 fuer jaehrlich
    person_id: Optional[int] = None     # betroffene Person, optional
    person_name: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date.isoformat(),
            "category": self.category,
            "description": self.description,
            "recurrence_days": self.recurrence_days,
            "person_id": self.person_id,
            "person": self.person_name,
        }


@dataclass
class SocialContact:
    """
    Ein wichtiger Mensch im Modul E (Soziale Pflege).

    'cadence_days' definiert, wie haeufig man sich melden moechte.
    """
    name: str
    relation: str = ""                  # Familie | Freund | Kollege | ...
    cadence_days: int = 30
    last_contacted: Optional[date] = None
    notes: str = ""
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "relation": self.relation,
            "cadence_days": self.cadence_days,
            "last_contacted": (self.last_contacted.isoformat()
                                if self.last_contacted else None),
            "notes": self.notes,
        }


@dataclass
class PriceMemory:
    """Preisgedaechtnis fuer wiederkehrende Einkaeufe (Modul B)."""
    product: str
    last_price: float
    last_seen: Optional[date] = None
    category: str = "sonstiges"
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product": self.product,
            "last_price": self.last_price,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "category": self.category,
        }


@dataclass
class AssistantLogEntry:
    """Persistente Spur einer Nutzer-Anfrage und der Antwort des Assistenten."""
    role: str                           # user | assistant | meta
    content: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class AuditLogEntry:
    """Eine Zeile im Audit-Log fuer destruktive/aenderne Aktionen."""
    action: str                         # z.B. 'contracts.delete'
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: str = ""
    actor: str = "local"
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "actor": self.actor,
        }


@dataclass
class TaskTemplate:
    """Vorlage fuer eine wiederkehrende Haushaltsaufgabe."""
    title: str
    interval_days: int = 7
    description: str = ""
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title,
                "interval_days": self.interval_days,
                "description": self.description}


@dataclass
class Note:
    """
    Freie Notiz. Optional an eine Entitaet angeheftet.

    'entity_type' ist eine der Modul-IDs ("contracts", "calendar",
    "social", "family", "expenses") oder None fuer eine freie Notiz.
    'entity_id' ist die ID des betroffenen Objekts (oder None).
    """
    title: str
    content: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
        }


@dataclass
class DayEntry:
    """Persistierter Tagebuch-Eintrag des Tagesstruktur-Moduls."""
    day: date
    level: int                          # 1..5
    note: str = ""
    id: Optional[int] = None
