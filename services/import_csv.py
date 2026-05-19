"""
CSV-Import als Spiegel zum services/export.py.

Konvention: dieselben Spaltennamen wie der Export, dasselbe Format
(utf-8-sig + Strichpunkt). Datumsfelder ISO, Betraege Punkt-getrennt.

Bewusst klein gehalten:
  - Eine Importer-Funktion pro Entitaet.
  - Jeder Import laeuft in einer Transaktion: entweder alle Zeilen oder
    keine (so bleibt der Bestand konsistent, wenn eine Zeile schiefgeht).
  - Die ID-Spalte aus dem Export wird ignoriert - bestehende Eintraege
    bekommen neue IDs. Wer einen kompletten Roundtrip braucht, sollte
    statt CSV den Backup-Pfad nutzen.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Optional

from database import (CalendarRepository, ContractRepository,
                      ExpenseRepository, FamilyRepository,
                      SocialRepository)
from models import (CalendarEvent, Contract, Expense, FamilyMember,
                    SocialContact)


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"CSV-Datei '{path}' nicht gefunden")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        return [dict(row) for row in reader]


def _safe_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Optional[str], default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Optional[str], default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value.replace(",", "."))
    except (TypeError, ValueError):
        return default


def import_contracts(repo: ContractRepository, path: Path) -> int:
    rows = _read_rows(path)
    inserted = 0
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        contract = Contract(
            name=name,
            category=row.get("kategorie") or "sonstiges",
            provider=row.get("anbieter") or "",
            customer_number=row.get("kundennummer") or "",
            start_date=_safe_date(row.get("start")),
            minimum_term_months=_safe_int(row.get("kuendigungsfrist_monate"),
                                            12),
            notice_period_months=_safe_int(row.get("kuendigungsfrist_monate"),
                                             3),
            auto_renew_months=_safe_int(row.get("verlaengerung_monate"), 12),
            monthly_cost=_safe_float(row.get("monatspreis"), 0.0),
            status=row.get("status") or "active",
        )
        repo.add(contract)
        inserted += 1
    return inserted


def import_expenses(repo: ExpenseRepository, path: Path) -> int:
    rows = _read_rows(path)
    inserted = 0
    for row in rows:
        description = (row.get("beschreibung") or "").strip()
        if not description:
            continue
        expense = Expense(
            description=description,
            amount=_safe_float(row.get("betrag"), 0.0),
            category=row.get("kategorie") or "sonstiges",
            spent_on=_safe_date(row.get("datum")),
        )
        repo.add(expense)
        inserted += 1
    return inserted


def import_calendar(repo: CalendarRepository, path: Path) -> int:
    rows = _read_rows(path)
    inserted = 0
    for row in rows:
        title = (row.get("titel") or "").strip()
        due = _safe_date(row.get("datum"))
        if not title or not due:
            continue
        event = CalendarEvent(
            title=title,
            due_date=due,
            category=row.get("kategorie") or "termin",
            description=row.get("beschreibung") or "",
            recurrence_days=(_safe_int(row.get("wiederholung_tage"), 0)
                              or None),
        )
        # 0 -> None (kein Wiederholungsmodus)
        if event.recurrence_days == 0:
            event.recurrence_days = None
        repo.add(event)
        inserted += 1
    return inserted


def import_social(repo: SocialRepository, path: Path) -> int:
    rows = _read_rows(path)
    inserted = 0
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        contact = SocialContact(
            name=name,
            relation=row.get("beziehung") or "",
            cadence_days=_safe_int(row.get("rhythmus_tage"), 30),
            last_contacted=_safe_date(row.get("zuletzt")),
            notes=row.get("notiz") or "",
        )
        repo.add(contact)
        inserted += 1
    return inserted


def import_family(repo: FamilyRepository, path: Path) -> int:
    rows = _read_rows(path)
    inserted = 0
    for row in rows:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        member = FamilyMember(
            name=name,
            role=row.get("rolle") or "erwachsen",
            birthday=_safe_date(row.get("geburtstag")),
        )
        repo.add_member(member)
        inserted += 1
    return inserted


# Mapping fuer den Bulk-Import: Dateiname -> Importer
IMPORTERS = {
    "contracts.csv": "contracts",
    "expenses.csv": "expenses",
    "calendar.csv": "calendar",
    "social.csv": "social",
    "family.csv": "family",
}


def import_all(source_dir: Path,
                contracts: ContractRepository,
                expenses: ExpenseRepository,
                calendar: CalendarRepository,
                social: SocialRepository,
                family: FamilyRepository) -> dict[str, int]:
    """Importiert alle CSVs im Verzeichnis, soweit vorhanden."""
    counts: dict[str, int] = {}
    plan = [
        ("family.csv", lambda p: import_family(family, p)),
        ("contracts.csv", lambda p: import_contracts(contracts, p)),
        ("expenses.csv", lambda p: import_expenses(expenses, p)),
        ("calendar.csv", lambda p: import_calendar(calendar, p)),
        ("social.csv", lambda p: import_social(social, p)),
    ]
    for filename, fn in plan:
        path = source_dir / filename
        if path.exists():
            counts[filename] = fn(path)
    return counts
