"""
Synthetische Testdaten gemaess Abschnitt 5 / Anhang G des Testkonzepts.

Liefert deterministische Profile (Seed = 42) fuer die Mitglieder-Szenarien
M-01 .. M-09 sowie generische Builder fuer Aufgaben, Auftraege und
Termine. Wird von allen Konzept-Tests verwendet, damit der gleiche
Datensatz reproduzierbar erzeugt werden kann.

Designprinzipien:
  - rein Python, keine Netz-/Cloud-Abhaengigkeiten
  - Tests koennen ueber `make_household(profile_id)` einen vollstaendig
    befuellten Repository-Stand bekommen
  - Profile sind Tupel aus (Name, FamilyMember-Liste, Aufgaben, Auftraege)
"""
from __future__ import annotations

import os
import random
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from database import (CalendarRepository, ContractRepository, Database,
                      ExpenseRepository, FamilyRepository, NoteRepository,
                      SettingsRepository, ShoppingRepository,
                      SocialRepository)
from models import (CalendarEvent, Contract, Expense, FamilyMember,
                    HouseholdOrder, HouseholdTask, ShoppingItem)


# ---------------------------------------------------------------------------
# Test-Status fuer Mitglieder (auf die App gemappt: aktiv | inaktiv |
# entfernt). "INVITED" wird simuliert ueber Mitglieder ohne Geburtstag und
# Rolle 'kind' (Onboarding noch nicht abgeschlossen) - dient nur dem
# konzeptuellen Test, ist nicht persistiert.
# ---------------------------------------------------------------------------
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_INVITED = "invited"
STATUS_REMOVED = "removed"


@dataclass
class MemberFixture:
    """Eine Person mit Konzept-Rolle + Konzept-Status."""
    name: str
    role: str             # "erwachsen" | "kind" | "sonstiges" (App-Domaene)
    concept_role: str     # OWNER | ADMIN | MEMBER | GUEST (Test-Konzept)
    status: str           # STATUS_*
    birthday: Optional[date] = None


@dataclass
class HouseholdFixture:
    """Vollstaendiger Haushalt fuer ein Szenario M-XX."""
    profile_id: str               # z.B. "M-03"
    label: str                    # z.B. "FAMILY_5"
    members: list[MemberFixture]
    tasks: list[HouseholdTask]
    orders: list[HouseholdOrder]
    expenses: list[Expense]
    calendar: list[CalendarEvent]


# ---------------------------------------------------------------------------
# Profilfabriken - jeweils deterministisch (Seed identisch zu Konzept G.1)
# ---------------------------------------------------------------------------
def _rng(seed: int) -> random.Random:
    return random.Random(seed)


def _make_members(profile_id: str, size: int, rng: random.Random
                  ) -> list[MemberFixture]:
    out: list[MemberFixture] = []
    today = date(2026, 5, 20)
    for i in range(size):
        if i == 0:
            concept = "OWNER"
            app_role = "erwachsen"
            status = STATUS_ACTIVE
        elif i == 1 and size >= 3:
            concept = "ADMIN"
            app_role = "erwachsen"
            status = STATUS_ACTIVE
        elif i % 7 == 0 and size > 6:
            concept = "GUEST"
            app_role = "sonstiges"
            status = STATUS_ACTIVE
        else:
            concept = "MEMBER"
            app_role = "erwachsen" if rng.random() < 0.6 else "kind"
            status = STATUS_ACTIVE
        # Streue Status-Varianten ab Profil ueber 5 Mitgliedern ein
        if size >= 6 and i in (size - 1,):
            status = STATUS_INVITED
        if size >= 11 and i == size - 2:
            status = STATUS_INACTIVE
        bd = today - timedelta(days=rng.randint(2000, 21000))
        out.append(MemberFixture(
            name=f"P{profile_id}-{i + 1:02d}",
            role=app_role,
            concept_role=concept,
            status=status,
            birthday=bd,
        ))
    return out


def _make_tasks(members: list[MemberFixture],
                count: int, rng: random.Random) -> list[HouseholdTask]:
    if not members:
        return []
    active = [m for m in members
              if m.status in (STATUS_ACTIVE, STATUS_INACTIVE)]
    if not active:
        active = members[:1]
    today = date(2026, 5, 20)
    intervals = [1, 7, 14, 30]
    out: list[HouseholdTask] = []
    for k in range(count):
        rotation_size = min(len(active), rng.randint(1, max(1, len(active))))
        rotation = [i for i in range(rotation_size)]
        out.append(HouseholdTask(
            title=f"Aufgabe-{k + 1:03d}",
            interval_days=rng.choice(intervals),
            next_due=today + timedelta(days=rng.randint(-5, 30)),
            rotation=list(rotation),
            current_index=0,
        ))
    return out


def _make_orders(members: list[MemberFixture], count: int,
                 rng: random.Random) -> list[HouseholdOrder]:
    if not members or count <= 0:
        return []
    today = date(2026, 5, 20)
    out: list[HouseholdOrder] = []
    for k in range(count):
        m = rng.choice([x for x in members if x.status == STATUS_ACTIVE]
                       or members)
        out.append(HouseholdOrder(
            title=f"Auftrag-{k + 1:03d}",
            assignee_name=m.name,
            due_date=today + timedelta(days=rng.randint(-2, 21)),
            description=f"synthetisch fuer {m.name}",
            status="offen",
        ))
    return out


def _make_expenses(members: list[MemberFixture], count: int,
                   rng: random.Random) -> list[Expense]:
    today = date(2026, 5, 20)
    out: list[Expense] = []
    for k in range(count):
        out.append(Expense(
            description=f"Posten-{k + 1:04d}",
            amount=round(rng.uniform(1.50, 120.00), 2),
            category=rng.choice(
                ["lebensmittel", "transport", "freizeit", "sonstiges"]),
            spent_on=today - timedelta(days=rng.randint(0, 30)),
            owner_name=(rng.choice(members).name if members else ""),
        ))
    return out


def _make_calendar(count: int, rng: random.Random) -> list[CalendarEvent]:
    today = date(2026, 5, 20)
    out: list[CalendarEvent] = []
    for k in range(count):
        out.append(CalendarEvent(
            title=f"Termin-{k + 1:03d}",
            due_date=today + timedelta(days=rng.randint(-2, 90)),
            category=rng.choice(
                ["termin", "garantie", "tuev", "steuer", "geburtstag"]),
            recurrence_days=(365 if k % 5 == 0 else None),
        ))
    return out


# Profil-Tabelle entsprechend TESTING.md Kapitel 2.1 / Anhang G
PROFILES: dict[str, tuple[str, int, int, int, int]] = {
    # profile_id : (label,     members, tasks, orders, expenses)
    "M-01":      ("SOLO",            1,    10,      0,        20),
    "M-02":      ("COUPLE",          2,    30,      4,        60),
    "M-03":      ("FAMILY_5",        5,    80,     10,       180),
    "M-04":      ("TEAM_11",        11,   150,     25,       420),
    "M-05":      ("BETA_12",        12,   200,     30,       500),
    "M-06":      ("STRESS_20",      20,   300,     40,       700),
    "M-07":      ("MIXED_STATUS",   12,   200,     30,       500),
    "M-08":      ("INVITED_ONLY",    6,    20,      2,        30),
    "M-09":      ("REACTIVATION",    8,    50,      5,       100),
}


def make_household(profile_id: str, seed: int = 42) -> HouseholdFixture:
    """Erzeugt einen vollstaendigen Haushalt fuer ein Profil-Kuerzel."""
    if profile_id not in PROFILES:
        raise KeyError(f"Unbekanntes Profil: {profile_id}")
    label, size, n_tasks, n_orders, n_exp = PROFILES[profile_id]
    rng = _rng(seed + sum(ord(c) for c in profile_id))
    members = _make_members(profile_id, size, rng)

    # Sonderbehandlung der Status-Varianten
    if profile_id == "M-07":
        for i, m in enumerate(members):
            if i < int(size * 0.6):
                m.status = STATUS_ACTIVE
            elif i < int(size * 0.8):
                m.status = STATUS_INVITED
            elif i < int(size * 0.9):
                m.status = STATUS_INACTIVE
            else:
                m.status = STATUS_REMOVED
    elif profile_id == "M-08":
        # Owner aktiv, alle anderen INVITED
        for i, m in enumerate(members):
            m.status = STATUS_ACTIVE if i == 0 else STATUS_INVITED
    elif profile_id == "M-09":
        # 1 Mitglied REMOVED, das wieder eingeladen wird (im Test)
        members[-1].status = STATUS_REMOVED

    tasks = _make_tasks(members, n_tasks, rng)
    orders = _make_orders(members, n_orders, rng)
    expenses = _make_expenses(members, n_exp, rng)
    calendar = _make_calendar(max(5, size * 2), rng)
    return HouseholdFixture(
        profile_id=profile_id, label=label, members=members,
        tasks=tasks, orders=orders, expenses=expenses, calendar=calendar)


# ---------------------------------------------------------------------------
# In-Memory-Repository-Bootstrap. Sorgt fuer voellige Isolation pro Test.
# ---------------------------------------------------------------------------
@dataclass
class RepoBundle:
    """Repositories + temporaere DB-Datei. close() raeumt auf."""
    db: Database
    path: str
    family: FamilyRepository
    contracts: ContractRepository
    expenses: ExpenseRepository
    shopping: ShoppingRepository
    calendar: CalendarRepository
    social: SocialRepository
    notes: NoteRepository
    settings: SettingsRepository

    def close(self) -> None:
        try:
            self.db.close()
        finally:
            try:
                os.unlink(self.path)
            except OSError:
                pass


def fresh_repos() -> RepoBundle:
    """Frischer SQLite-Stand in einer Temporaerdatei (auto-migriert)."""
    fd, path = tempfile.mkstemp(prefix="zunarodo-test-", suffix=".db")
    os.close(fd)
    db = Database(path=path)
    return RepoBundle(
        db=db, path=path,
        family=FamilyRepository(db),
        contracts=ContractRepository(db),
        expenses=ExpenseRepository(db),
        shopping=ShoppingRepository(db),
        calendar=CalendarRepository(db),
        social=SocialRepository(db),
        notes=NoteRepository(db),
        settings=SettingsRepository(db),
    )


def seed_household(repos: RepoBundle, fixture: HouseholdFixture
                   ) -> dict[str, FamilyMember]:
    """
    Speichert die Mitglieder, Aufgaben, Auftraege etc. eines Fixtures in
    den Repositories und gibt Name->FamilyMember-Map zurueck.

    Mitglieder mit STATUS_REMOVED werden zuerst angelegt und dann
    soft-geloescht. Mitglieder mit STATUS_INVITED werden als Member
    angelegt, aber nicht in Rotationen verwendet (siehe Anwender).
    """
    name_to_member: dict[str, FamilyMember] = {}
    for mf in fixture.members:
        m = FamilyMember(name=mf.name, role=mf.role, birthday=mf.birthday)
        repos.family.add_member(m)
        name_to_member[mf.name] = m
        if mf.status == STATUS_REMOVED:
            assert m.id is not None
            repos.family.soft_delete_member(m.id)

    # Aufgaben mit Rotation aus den persistierten IDs
    active_ids = [name_to_member[m.name].id for m in fixture.members
                  if m.status == STATUS_ACTIVE
                  and name_to_member[m.name].id is not None]
    for task in fixture.tasks:
        if not active_ids:
            break
        rotation_size = max(1, min(len(active_ids), len(task.rotation) or 1))
        task_with_rot = HouseholdTask(
            title=task.title,
            interval_days=task.interval_days,
            next_due=task.next_due,
            rotation=active_ids[:rotation_size],
            current_index=task.current_index,
        )
        repos.family.add_task(task_with_rot)

    for order in fixture.orders:
        m = name_to_member.get(order.assignee_name)
        repos.family.add_order(HouseholdOrder(
            title=order.title,
            assignee_id=(m.id if m else None),
            assignee_name=order.assignee_name,
            due_date=order.due_date,
            description=order.description,
            status=order.status,
        ))

    for exp in fixture.expenses:
        m = name_to_member.get(exp.owner_name)
        repos.expenses.add(Expense(
            description=exp.description, amount=exp.amount,
            category=exp.category, spent_on=exp.spent_on,
            owner_id=(m.id if m else None), owner_name=exp.owner_name,
        ))

    for ev in fixture.calendar:
        repos.calendar.add(ev)

    return name_to_member
