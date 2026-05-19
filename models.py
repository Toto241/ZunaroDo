"""
Domänenmodelle des Alltagshelfers.

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
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """JSON-serialisierbare Darstellung - das Format der Schnittstelle."""
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
        }


@dataclass
class Deadline:
    """Eine errechnete Frist, die zu einem Vertrag gehoert."""
    contract_id: int
    type: str                           # cancellation | renewal | price_change
    due_date: date
    title: str
    resolved: bool = False
    id: Optional[int] = None
    # nur fuer die Anzeige, nicht persistiert:
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


@dataclass
class Expense:
    """Eine einmalige Ausgabe (Modul B - Finanzen)."""
    description: str
    amount: float
    category: str = "sonstiges"         # lebensmittel | freizeit | mobilitaet ...
    spent_on: Optional[date] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "spent_on": self.spent_on.isoformat() if self.spent_on else None,
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
    """
    Ein anstehendes Ereignis fuer das Dashboard - modul-uebergreifend.

    Jedes Modul liefert seine Ereignisse in genau diesem Format. Das
    Dashboard kann sie dadurch zusammenfuehren, ohne die Module zu kennen.
    """
    title: str
    due_date: date
    module_id: str
    module_name: str
    category: str = "erinnerung"        # frist | zahlung | review | erinnerung
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
    role: str = "erwachsen"             # erwachsen | kind | sonstiges
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "role": self.role}


@dataclass
class HouseholdTask:
    """
    Eine wiederkehrende Haushaltsaufgabe mit Rotation (Modul D).

    'rotation' ist die Reihenfolge der Mitglieder-IDs; 'current_index'
    zeigt auf das aktuell zustaendige Mitglied. Beim Abhaken rueckt der
    Index weiter und 'next_due' wird um 'interval_days' verschoben.
    """
    title: str
    interval_days: int = 7              # Wiederholungsintervall
    next_due: Optional[date] = None
    rotation: list[int] = field(default_factory=list)   # Mitglieder-IDs
    current_index: int = 0
    id: Optional[int] = None
    current_assignee_name: str = ""     # nur Anzeige, nicht persistiert

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
    """
    Ein einmaliger Auftrag (Modul D) - gezielt einer Person zugewiesen,
    mit Termin und Status. Abgrenzung zu HouseholdTask: einmalig + gezielt
    statt wiederkehrend + rotierend.
    """
    title: str
    assignee_id: Optional[int] = None
    due_date: Optional[date] = None
    description: str = ""
    status: str = "offen"               # offen | erledigt
    id: Optional[int] = None
    assignee_name: str = ""             # nur Anzeige

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "assignee": self.assignee_name,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "description": self.description,
            "status": self.status,
        }


@dataclass
class Proposal:
    """
    Ein Vorschlag in der zentralen Vorschlags-Ablage.

    Entsteht z.B. aus einer Mail-Analyse. Er nennt eine Ziel-Capability
    und die fertige Nutzlast. Bei Bestaetigung wird genau diese Capability
    aufgerufen - das zustaendige Modul prueft und uebernimmt die Daten.
    Nichts wird ungeprueft ins System geschrieben.
    """
    source: str                         # z.B. "mail"
    summary: str                        # menschenlesbare Kurzbeschreibung
    target_capability: str              # z.B. "contracts.add"
    payload: dict = field(default_factory=dict)
    status: str = "offen"               # offen | uebernommen | abgelehnt
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
