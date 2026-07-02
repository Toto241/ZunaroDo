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
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from database import (CalendarRepository, ContractRepository,
                      ExpenseRepository, FamilyRepository,
                      ProposalRepository, SocialRepository)


def _sanitize_cell(value: Any) -> Any:
    """Neutralisiert CSV-Formel-Injection.

    Excel/LibreOffice/Google Sheets interpretieren Zellen, die mit
    = + - @ (oder einem fuehrenden Tab/CR) beginnen, beim Oeffnen als
    Formel. Ein Nutzer, der z.B. einen Vertragsnamen wie
    '=HYPERLINK(<url>,...)' eingibt, koennte so beim Oeffnen des
    Exports Netzwerkzugriffe/Code ausloesen. Solchen String-Werten wird
    ein Hochkomma vorangestellt (uebliche Schutzpraxis) - die Tabellen-
    kalkulation behandelt die Zelle dann als Text. Nicht-Strings (Zahlen,
    Datumsobjekte) bleiben unveraendert.
    """
    if isinstance(value, str) and value and value[0] in "=+-@\t\r":
        return "'" + value
    return value


def _write(path: Path, headers: list[str],
            rows: Iterable[list]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(headers)
        for row in rows:
            writer.writerow([_sanitize_cell(c) for c in row])
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


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"Nicht serialisierbar: {type(obj)!r}")


def export_all_json(target_dir: Path, contracts: ContractRepository,
                    expenses: ExpenseRepository,
                    calendar: CalendarRepository,
                    social: SocialRepository,
                    family: FamilyRepository,
                    *,
                    include_settings: bool = False,
                    settings_rows: (dict[str, str]
                                     | list[tuple[str, str]] | None) = None
                    ) -> Path:
    """
    Ein JSON-Bundle mit allen Hauptentitaeten (DSGVO-Datenexport).

    Liefert den Pfad zur geschriebenen Datei.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "format": "zunarodo-export-v1",
        "contracts": [c.to_dict() for c in contracts.list_all(only_active=False)],
        "expenses": [e.to_dict() for e in expenses.list_all()],
        "calendar": [e.to_dict() for e in calendar.list_all()],
        "social": [c.to_dict() for c in social.list_all()],
        "family": [m.to_dict() for m in family.list_members()],
    }
    if include_settings and settings_rows is not None:
        rows = (settings_rows.items()
                if isinstance(settings_rows, dict) else settings_rows)
        payload["settings"] = [
            {"key": k, "value": v} for k, v in rows
            if not k.startswith(("gemini_", "imap_", "smtp_", "license.token"))
        ]
    out = target_dir / "export.json"
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return out


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
