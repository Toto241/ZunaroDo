"""
Negativtests Block A - Benutzerbezogene Eingaben (TESTING.md Abschnitt 11.3 A).

Ziel: Die App darf bei manipulierten/extremen Eingaben weder abstuerzen
noch Daten korrumpieren noch SQL-Injection zulassen. Wir testen gegen
die echte Datenschicht (parameterisierte SQLite-Queries) und gegen die
Module-Capability-Schicht.

Abgedeckte N-IDs:

  N-A-02  extrem lange Eingaben (10000+ Zeichen)
  N-A-03  Sonderzeichen (Emoji, Steuerzeichen, NUL, RTL)
  N-A-04  SQL-Injection-aehnliche Eingaben
  N-A-05  Doppel-Insert (gleicher Name)
  N-A-11  Unvollstaendiges Profil (Pflichtparameter fehlt)
"""
from __future__ import annotations

from datetime import date

import pytest

from core.interface import ModuleRegistry
from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, NoteRepository,
                      ProposalRepository, ShoppingRepository,
                      SocialRepository)
from models import Contract, Expense, FamilyMember
from modules.calendar import CalendarModule
from modules.contracts import ContractModule
from modules.family import FamilyModule
from modules.finance import FinanceModule
from modules.inbox import InboxModule
from modules.notes import NotesModule
from modules.social import SocialModule

from .fixtures import fresh_repos


# Marker, damit der Protokoll-Generator den Bereich erkennt
pytestmark = [pytest.mark.concept, pytest.mark.negative]


@pytest.fixture
def repos():
    bundle = fresh_repos()
    try:
        yield bundle
    finally:
        bundle.close()


@pytest.fixture
def registry(repos):
    reg = ModuleRegistry()
    reg.register(FamilyModule(repos.family, repos.shopping))
    reg.register(ContractModule(repos.contracts))
    reg.register(FinanceModule(repos.expenses))
    reg.register(CalendarModule(repos.calendar))
    reg.register(SocialModule(repos.social))
    reg.register(NotesModule(repos.notes))
    reg.register(InboxModule(ProposalRepository(repos.db)))
    return reg


# ---------------------------------------------------------------------------
# N-A-02 extrem lange Eingaben
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("length", [1024, 10_000, 65_536])
def test_NA02_long_member_name_is_stored_or_rejected(repos, length):
    """Sehr lange Namen duerfen nicht crashen.

    Akzeptanzkriterium: Entweder die DB speichert literal (parameterized),
    oder ein definierter Fehler kommt zurueck - aber kein Crash und keine
    Datenkorruption (Repository-Listing bleibt parsebar).
    """
    big = "X" * length
    repos.family.add_member(FamilyMember(name=big, role="erwachsen"))
    members = repos.family.list_members()
    assert any(m.name == big for m in members)
    # Re-Read auch fehlerfrei
    found = repos.family.find_member_by_name(big)
    assert found is not None and len(found.name) == length


def test_NA02_long_contract_name_does_not_break_listing(repos):
    big = "Vertrag-" + "Y" * 9000
    c = repos.contracts.add(Contract(
        name=big, category="streaming", monthly_cost=9.99))
    assert c.id is not None
    contracts = repos.contracts.list_all()
    assert any(x.id == c.id for x in contracts)


# ---------------------------------------------------------------------------
# N-A-03 Sonderzeichen
# ---------------------------------------------------------------------------
SPECIAL_INPUTS = [
    "Anna \U0001F600",                # Emoji
    "Anna\x00Nachher",                 # NUL-Byte
    "Anna\nMehrzeilig",                # Zeilenumbruch
    "‮arabicRTL",                 # RTL-Override
    "  trailing space   ",
    "<script>alert(1)</script>",       # XSS-aehnliche Payload
    "Anna' DROP",                       # SQL-aehnliche Sequenz, einzeln
    "Анна Иванова",                    # kyrillisch
    "山田太郎",                        # CJK
    " ",                                # nur Whitespace
]


@pytest.mark.parametrize("name", SPECIAL_INPUTS,
                          ids=lambda n: repr(n)[:24])
def test_NA03_special_chars_in_member_name(repos, name):
    repos.family.add_member(FamilyMember(name=name, role="erwachsen"))
    members = repos.family.list_members()
    # Wir verlangen nicht 100 % Erhalt (Trim ist erlaubt), aber:
    #  - kein Absturz
    #  - mind. 1 zusaetzliches Mitglied
    #  - jeder Name ist re-serialisierbar
    assert members, "Liste darf nicht leer sein"
    for m in members:
        assert m.to_dict()["name"] == m.name


@pytest.mark.parametrize("payload", SPECIAL_INPUTS,
                          ids=lambda n: repr(n)[:24])
def test_NA03_special_chars_in_expense_description(repos, payload):
    repos.expenses.add(Expense(
        description=payload, amount=1.50, spent_on=date(2026, 5, 20)))
    items = repos.expenses.list_all()
    assert items


# ---------------------------------------------------------------------------
# N-A-04 SQL-Injection
# ---------------------------------------------------------------------------
SQL_PAYLOADS = [
    "Anna'; DROP TABLE family_members; --",
    "1' OR '1'='1",
    "'); DELETE FROM contracts; --",
    "Anna\"; UPDATE family_members SET name='gehackt'--",
    "Anna\\'; SELECT * FROM sqlite_master; --",
    "%27%20OR%201=1%20--%20",
]


@pytest.mark.parametrize("payload", SQL_PAYLOADS,
                          ids=lambda n: n[:20])
def test_NA04_sql_injection_in_member_name_is_literal(repos, payload):
    """Parameter-Binding muss eine Injection wie eine normale Zeichen­
    kette behandeln. Wir verifizieren, dass Tabelle weiter existiert und
    das Mitglied LITERAL gespeichert wurde."""
    repos.family.add_member(FamilyMember(name=payload, role="erwachsen"))
    found = repos.family.find_member_by_name(payload)
    assert found is not None, "Eingabe wurde nicht persistiert"
    assert found.name == payload, "SQL-Injection-Eingabe wurde umgeschrieben"

    # Schemata sind unveraendert
    cur = repos.db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in cur}
    assert "family_members" in tables, "Injection hat eine Tabelle entfernt!"
    assert "contracts" in tables, "Injection hat 'contracts' entfernt!"


@pytest.mark.parametrize("payload", SQL_PAYLOADS, ids=lambda n: n[:20])
def test_NA04_sql_injection_in_contract_fields(repos, payload):
    c = repos.contracts.add(Contract(
        name=payload, category=payload, provider=payload,
        monthly_cost=1.0, notes=payload))
    assert c.id is not None
    again = repos.contracts.get(c.id)
    assert again is not None
    assert again.name == payload


# ---------------------------------------------------------------------------
# N-A-05 Doppelter Account / doppeltes Mitglied
# ---------------------------------------------------------------------------
def test_NA05_double_member_is_idempotent_or_distinct_ids(repos):
    """Die App-Domaene erlaubt gleichnamige Mitglieder (zwei Annas im
    Haushalt). Wir verlangen entweder eindeutige IDs ODER eine
    deklarierte Fehlermeldung - aber keinen stillen Datenverlust."""
    m1 = repos.family.add_member(FamilyMember(name="Anna", role="erwachsen"))
    m2 = repos.family.add_member(FamilyMember(name="Anna", role="erwachsen"))
    assert m1.id != m2.id, ("Doppelte Inserts muessen unterscheidbare IDs "
                              "erhalten")


# ---------------------------------------------------------------------------
# N-A-11 Unvollstaendiges Profil / fehlende Pflichtparameter
# ---------------------------------------------------------------------------
def test_NA11_missing_required_param_returns_friendly_error(registry):
    result = registry.dispatch("family.add_member", {})  # name fehlt
    assert "error" in result
    assert "Pflichtparameter" in result["error"] or "name" in result["error"]


def test_NA11_unknown_capability_returns_friendly_error(registry):
    result = registry.dispatch("does.not.exist", {"foo": "bar"})
    assert "error" in result
    assert "nicht gefunden" in result["error"]


def test_NA11_invalid_param_type_does_not_crash(registry):
    """Falsche Typen (string statt int) duerfen die Capability nicht
    crashen - sie muessen einen sauberen Fehler zurueckgeben."""
    result = registry.dispatch(
        "family.delete_member", {"member_id": "not-an-int"})
    # Entweder explizit als Error oder als TypeError-gefangener Fehler
    assert "error" in result or result.get("ok") is False
