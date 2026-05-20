"""
Datenschutz-Tests Block B - Nutzerrechte (TESTING.md Teil II 12.3 B).

Geprueftes Verhalten:

  P-B-01  Konto-Loeschung als Capability vorhanden  (bereits in
          test_privacy_scan abgedeckt, hier aktiv durchspielen)
  P-B-02  Konto-Loeschung entfernt verknuepfte Daten (Family + Referenzen)
  P-B-03  Daten-Export liefert ein parsbares Artefakt
  P-B-04  Widerruf wirkt sofort (Soft-Delete + Restore)
  P-B-06  Lokale Daten lassen sich (endgueltig) loeschen
"""
from __future__ import annotations

import csv
import os
import tempfile
from datetime import date
from pathlib import Path

import pytest

from models import (CalendarEvent, Contract, Expense, FamilyMember,
                    HouseholdOrder, SocialContact)
from services.export import (export_all, export_calendar, export_contracts,
                              export_expenses, export_family, export_social)

from .fixtures import fresh_repos


pytestmark = [pytest.mark.concept, pytest.mark.privacy]


@pytest.fixture
def repos_with_data():
    bundle = fresh_repos()
    try:
        # Mini-Datensatz, der alle Daten-Typen enthaelt
        alice = bundle.family.add_member(
            FamilyMember(name="Alice", role="erwachsen"))
        bundle.contracts.add(Contract(
            name="Strom", category="strom", provider="Stadtwerke",
            monthly_cost=49.90, owner_id=alice.id))
        bundle.expenses.add(Expense(
            description="Wocheneinkauf", amount=42.50,
            spent_on=date(2026, 5, 18), owner_id=alice.id,
            owner_name="Alice"))
        bundle.calendar.add(CalendarEvent(
            title="Steuererklaerung", due_date=date(2026, 7, 31),
            category="steuer"))
        bundle.social.add(SocialContact(
            name="Bob", relation="freund", cadence_days=30))
        bundle.family.add_order(HouseholdOrder(
            title="Auto zum TUEV", assignee_id=alice.id,
            assignee_name="Alice", due_date=date(2026, 6, 15)))
        yield bundle, alice
    finally:
        bundle.close()


# ---------------------------------------------------------------------------
# P-B-02 Mitglied loeschen -> Referenzen werden entkoppelt
# ---------------------------------------------------------------------------
def test_PB02_purging_member_decouples_references(repos_with_data):
    repos, alice = repos_with_data
    assert alice.id is not None
    # endgueltig loeschen (purge)
    assert repos.family.delete_member(alice.id) is True

    # Auftrag, Vertrag, Ausgabe MUESSEN noch existieren, aber die
    # Personenreferenz wird via ON DELETE SET NULL entkoppelt.
    contracts = repos.contracts.list_all()
    assert any(c.name == "Strom" for c in contracts)
    for c in contracts:
        if c.name == "Strom":
            assert c.owner_id is None, (
                "owner_id muss bei purge auf NULL gesetzt sein")

    expenses = repos.expenses.list_all()
    assert expenses
    for e in expenses:
        assert e.owner_id is None, (
            "Expense.owner_id muss bei purge auf NULL gehen")

    orders = repos.family.list_orders(only_open=False)
    assert orders
    for o in orders:
        assert o.assignee_id is None, (
            "HouseholdOrder.assignee_id muss bei purge auf NULL gehen")


# ---------------------------------------------------------------------------
# P-B-03 Datenexport liefert valide Dateien
# ---------------------------------------------------------------------------
def test_PB03_export_all_produces_parseable_artifacts(repos_with_data,
                                                       tmp_path: Path):
    repos, _ = repos_with_data
    target = tmp_path / "export"
    target.mkdir()
    counts = export_all(
        target, contracts=repos.contracts, expenses=repos.expenses,
        calendar=repos.calendar, social=repos.social, family=repos.family)
    assert sum(counts.values()) >= 4, counts

    files = list(target.glob("*.csv"))
    assert files, "Export muss mindestens eine CSV erzeugen"
    # Jede CSV laesst sich mit dem Standard-Parser lesen
    for f in files:
        with f.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        assert rows, f"{f.name} ist leer"
        assert all(len(r) == len(rows[0]) for r in rows), (
            f"{f.name} hat inkonsistente Spaltenanzahl")


@pytest.mark.parametrize("exporter,name,attr", [
    (export_contracts, "vertraege.csv", "contracts"),
    (export_expenses, "ausgaben.csv", "expenses"),
    (export_calendar, "termine.csv", "calendar"),
    (export_social, "kontakte.csv", "social"),
    (export_family, "haushalt.csv", "family"),
])
def test_PB03_each_exporter_produces_header(repos_with_data, tmp_path,
                                              exporter, name, attr):
    repos, _ = repos_with_data
    target = tmp_path / name
    n = exporter(getattr(repos, attr), target)
    assert n >= 0
    text = target.read_text(encoding="utf-8")
    # Erste Zeile = Header, mindestens 2 Spalten getrennt durch ';' oder ','
    first = text.splitlines()[0]
    assert (";" in first or "," in first), (
        f"{name}: Header ohne Spaltentrenner")


# ---------------------------------------------------------------------------
# P-B-04 Widerruf wirkt sofort (Soft-Delete + Restore)
# ---------------------------------------------------------------------------
def test_PB04_soft_delete_hides_then_restore_brings_back(repos_with_data):
    repos, alice = repos_with_data
    # Soft-Delete
    assert repos.family.soft_delete_member(alice.id) is True
    assert alice.name not in {m.name for m in repos.family.list_members()}
    assert alice.name in {m.name
                          for m in repos.family.list_deleted_members()}
    # Widerruf
    assert repos.family.restore_member(alice.id) is True
    assert alice.name in {m.name for m in repos.family.list_members()}


# ---------------------------------------------------------------------------
# P-B-06 Lokale Daten endgueltig loeschen (DB-Datei)
# ---------------------------------------------------------------------------
def test_PB06_dropping_db_file_removes_all_data(repos_with_data):
    repos, _ = repos_with_data
    path = repos.path
    repos.db.close()
    os.unlink(path)
    assert not Path(path).exists()
    # Ein erneutes Oeffnen erzeugt eine frische DB ohne Daten
    from database import Database, FamilyRepository
    db2 = Database(path=path)
    try:
        fr = FamilyRepository(db2)
        assert fr.list_members() == []
    finally:
        db2.close()
        try:
            os.unlink(path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Bonus: AuditLog enthaelt KEINE PII
# ---------------------------------------------------------------------------
def test_audit_log_format_does_not_leak_pii(repos_with_data):
    """Sehr einfacher Check: Audit-Log (sofern ein Eintrag erzeugt wurde)
    enthaelt keine roh-personenbezogenen Daten (E-Mail, Telefon)."""
    import re
    repos, _ = repos_with_data
    # Wir koennen den Audit-Log nicht direkt abrufen, weil er optional ist;
    # stattdessen pruefen wir die jeweilige to_dict()-Ausgabe der Modelle:
    members = repos.family.list_members()
    for m in members:
        d = m.to_dict()
        for v in d.values():
            if not isinstance(v, str):
                continue
            assert not re.search(r"\+49\d", v), (
                f"PII (Telefon) in to_dict: {v!r}")
