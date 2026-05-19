"""
CSV-Export der Hauptdaten.

Format: utf-8-sig (BOM, damit Excel-DE die Spalten korrekt erkennt) und
Strichpunkt als Trennzeichen - Excel-Standardeinstellung in der
deutschsprachigen Region. Datum: ISO (YYYY-MM-DD). Betraege werden
mit Punkt als Dezimaltrennzeichen exportiert - Excel-DE wandelt das
beim Import in Komma.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from database import (CalendarRepository, ContractRepository,
                      ExpenseRepository, FamilyRepository,
                      ProposalRepository, SocialRepository)


def _write(path: Path, headers: list[str],
            rows: Iterable[list]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def export_contracts(repo: ContractRepository, path: Path) -> int:
    return _write(
        path,
        ["id", "name", "kategorie", "anbieter", "kundennummer",
         "start", "monatspreis", "kuendigungsfrist_monate",
         "verlaengerung_monate", "person", "status"],
        [[c.id, c.name, c.category, c.provider, c.customer_number,
          c.start_date.isoformat() if c.start_date else "",
          f"{c.monthly_cost:.2f}", c.notice_period_months,
          c.auto_renew_months, c.owner_name, c.status]
         for c in repo.list_all(only_active=False)]
    )


def export_expenses(repo: ExpenseRepository, path: Path) -> int:
    return _write(
        path,
        ["id", "datum", "beschreibung", "betrag", "kategorie", "person"],
        [[e.id, e.spent_on.isoformat() if e.spent_on else "",
          e.description, f"{e.amount:.2f}",
          e.category, e.owner_name]
         for e in repo.list_all()]
    )


def export_calendar(repo: CalendarRepository, path: Path) -> int:
    return _write(
        path,
        ["id", "datum", "titel", "kategorie", "person",
         "wiederholung_tage", "beschreibung"],
        [[e.id, e.due_date.isoformat(), e.title, e.category,
          e.person_name, e.recurrence_days or "", e.description]
         for e in repo.list_all()]
    )


def export_social(repo: SocialRepository, path: Path) -> int:
    return _write(
        path,
        ["id", "name", "beziehung", "rhythmus_tage", "zuletzt", "notiz"],
        [[c.id, c.name, c.relation, c.cadence_days,
          c.last_contacted.isoformat() if c.last_contacted else "",
          c.notes]
         for c in repo.list_all()]
    )


def export_family(repo: FamilyRepository, path: Path) -> int:
    return _write(
        path,
        ["id", "name", "rolle", "geburtstag"],
        [[m.id, m.name, m.role,
          m.birthday.isoformat() if m.birthday else ""]
         for m in repo.list_members()]
    )


# Mapping von Schluessel auf Export-Funktion + DB-Repo-Klasse - so
# kann die CLI/GUI einfach "alle Entitaeten" durchlaufen.
EXPORTERS: dict[str, str] = {
    "contracts": "Vertraege",
    "expenses": "Ausgaben",
    "calendar": "Termine",
    "social": "Kontakte",
    "family": "Haushaltsmitglieder",
}


def export_all(target_dir: Path, contracts: ContractRepository,
                expenses: ExpenseRepository,
                calendar: CalendarRepository,
                social: SocialRepository,
                family: FamilyRepository) -> dict[str, int]:
    """Exportiert alle Entitaeten in ein Verzeichnis. Liefert die Counts."""
    target_dir.mkdir(parents=True, exist_ok=True)
    return {
        "contracts": export_contracts(contracts, target_dir / "contracts.csv"),
        "expenses": export_expenses(expenses, target_dir / "expenses.csv"),
        "calendar": export_calendar(calendar, target_dir / "calendar.csv"),
        "social": export_social(social, target_dir / "social.csv"),
        "family": export_family(family, target_dir / "family.csv"),
    }
