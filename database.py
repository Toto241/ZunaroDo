"""
Datenschicht - SQLite.

Diese Schicht kennt nur Speicherung. Sie weiss nichts vom KI-Assistenten.
Der Zugriff laeuft ueber das Repository, das Domaenenobjekte zurueckgibt.

Hinweis Datenschutz: In Produktion sollte die DB mit SQLCipher
verschluesselt werden - dafuer 'pysqlcipher3' statt 'sqlite3' nutzen.
Da pysqlcipher3 auf Windows oft Build-Schritte braucht, ist es hier
ein optionales Upgrade, kein Default.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

from models import (AssistantLogEntry, CalendarEvent, Contract, Expense,
                    FamilyMember, HouseholdOrder, HouseholdTask, PriceMemory,
                    Proposal, ShoppingItem, SocialContact)

SCHEMA = """
CREATE TABLE IF NOT EXISTS contracts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    category             TEXT NOT NULL,
    provider             TEXT DEFAULT '',
    customer_number      TEXT DEFAULT '',
    start_date           TEXT,
    minimum_term_months  INTEGER DEFAULT 12,
    notice_period_months INTEGER DEFAULT 3,
    auto_renew_months    INTEGER DEFAULT 12,
    monthly_cost         REAL DEFAULT 0.0,
    currency             TEXT DEFAULT 'EUR',
    notes                TEXT DEFAULT '',
    status               TEXT DEFAULT 'active',
    owner_id             INTEGER,
    created_at           TEXT,
    updated_at           TEXT,
    FOREIGN KEY (owner_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS price_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    old_cost    REAL,
    new_cost    REAL,
    changed_at  TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount      REAL NOT NULL,
    category    TEXT DEFAULT 'sonstiges',
    spent_on    TEXT,
    owner_id    INTEGER,
    created_at  TEXT,
    FOREIGN KEY (owner_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS family_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    role       TEXT DEFAULT 'erwachsen',
    birthday   TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS household_tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    interval_days INTEGER DEFAULT 7,
    next_due      TEXT,
    current_index INTEGER DEFAULT 0,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS task_rotation (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id   INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    position  INTEGER NOT NULL,
    FOREIGN KEY (task_id)   REFERENCES household_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES family_members(id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS household_orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    assignee_id INTEGER,
    due_date    TEXT,
    description TEXT DEFAULT '',
    status      TEXT DEFAULT 'offen',
    created_at  TEXT,
    FOREIGN KEY (assignee_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS shopping_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    quantity    TEXT DEFAULT '',
    added_by_id INTEGER,
    bought      INTEGER DEFAULT 0,
    created_at  TEXT,
    FOREIGN KEY (added_by_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS proposals (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT,
    summary           TEXT,
    target_capability TEXT,
    payload           TEXT,
    status            TEXT DEFAULT 'offen',
    created_at        TEXT
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    due_date        TEXT NOT NULL,
    category        TEXT DEFAULT 'termin',
    description     TEXT DEFAULT '',
    recurrence_days INTEGER,
    person_id       INTEGER,
    created_at      TEXT,
    FOREIGN KEY (person_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS social_contacts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    relation       TEXT DEFAULT '',
    cadence_days   INTEGER DEFAULT 30,
    last_contacted TEXT,
    notes          TEXT DEFAULT '',
    created_at     TEXT
);

CREATE TABLE IF NOT EXISTS price_memory (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product    TEXT NOT NULL UNIQUE,
    last_price REAL,
    last_seen  TEXT,
    category   TEXT DEFAULT 'sonstiges',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS assistant_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT,
    content    TEXT,
    created_at TEXT
);
"""


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Liest die existierenden Spaltennamen einer Tabelle."""
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _ensure_column(conn: sqlite3.Connection, table: str,
                   column: str, ddl_type: str) -> None:
    """Migration: fuegt eine Spalte hinzu, falls sie noch nicht existiert."""
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")


class Database:
    """Duenne Wrapper-Klasse um die SQLite-Verbindung."""

    def __init__(self, path: str = "alltagshelfer.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        """Spalten, die in alten DBs noch fehlen, nachziehen."""
        _ensure_column(self.conn, "contracts", "owner_id", "INTEGER")
        _ensure_column(self.conn, "expenses", "owner_id", "INTEGER")
        _ensure_column(self.conn, "family_members", "birthday", "TEXT")

    def close(self) -> None:
        self.conn.close()


# =====================================================================
#  Vertraege (Modul A)
# =====================================================================
class ContractRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, c: Contract) -> Contract:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            """INSERT INTO contracts
               (name, category, provider, customer_number, start_date,
                minimum_term_months, notice_period_months, auto_renew_months,
                monthly_cost, currency, notes, status, owner_id,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (c.name, c.category, c.provider, c.customer_number,
             c.start_date.isoformat() if c.start_date else None,
             c.minimum_term_months, c.notice_period_months,
             c.auto_renew_months, c.monthly_cost, c.currency,
             c.notes, c.status, c.owner_id, now, now),
        )
        self.db.conn.commit()
        c.id = cur.lastrowid
        return c

    def update_cost(self, contract_id: int, new_cost: float) -> None:
        old = self.get(contract_id)
        if old is None:
            raise ValueError(f"Vertrag {contract_id} existiert nicht")
        now = datetime.now().isoformat(timespec="seconds")
        self.db.conn.execute(
            "INSERT INTO price_history (contract_id, old_cost, new_cost, changed_at)"
            " VALUES (?,?,?,?)",
            (contract_id, old.monthly_cost, new_cost, now),
        )
        self.db.conn.execute(
            "UPDATE contracts SET monthly_cost=?, updated_at=? WHERE id=?",
            (new_cost, now, contract_id),
        )
        self.db.conn.commit()

    def set_status(self, contract_id: int, status: str) -> None:
        self.db.conn.execute(
            "UPDATE contracts SET status=?, updated_at=? WHERE id=?",
            (status, datetime.now().isoformat(timespec="seconds"), contract_id),
        )
        self.db.conn.commit()

    def set_owner(self, contract_id: int, owner_id: Optional[int]) -> None:
        self.db.conn.execute(
            "UPDATE contracts SET owner_id=?, updated_at=? WHERE id=?",
            (owner_id, datetime.now().isoformat(timespec="seconds"),
             contract_id))
        self.db.conn.commit()

    def get(self, contract_id: int) -> Optional[Contract]:
        row = self.db.conn.execute(
            "SELECT c.*, m.name AS owner_name FROM contracts c"
            " LEFT JOIN family_members m ON m.id = c.owner_id"
            " WHERE c.id=?", (contract_id,)
        ).fetchone()
        return self._row_to_contract(row) if row else None

    def list_all(self, only_active: bool = True) -> list[Contract]:
        sql = ("SELECT c.*, m.name AS owner_name FROM contracts c"
               " LEFT JOIN family_members m ON m.id = c.owner_id")
        if only_active:
            sql += " WHERE c.status='active'"
        sql += " ORDER BY c.name"
        return [self._row_to_contract(r) for r in self.db.conn.execute(sql)]

    def price_changes(self, contract_id: int) -> list[dict]:
        rows = self.db.conn.execute(
            "SELECT old_cost, new_cost, changed_at FROM price_history"
            " WHERE contract_id=? ORDER BY changed_at DESC",
            (contract_id,),
        )
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_contract(row: sqlite3.Row) -> Contract:
        return Contract(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            provider=row["provider"],
            customer_number=row["customer_number"],
            start_date=date.fromisoformat(row["start_date"]) if row["start_date"] else None,
            minimum_term_months=row["minimum_term_months"],
            notice_period_months=row["notice_period_months"],
            auto_renew_months=row["auto_renew_months"],
            monthly_cost=row["monthly_cost"],
            currency=row["currency"],
            notes=row["notes"],
            status=row["status"],
            owner_id=row["owner_id"],
            owner_name=(row["owner_name"] or "") if "owner_name" in row.keys() else "",
        )


# =====================================================================
#  Finanzen (Modul B)
# =====================================================================
class ExpenseRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, e: Expense) -> Expense:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO expenses (description, amount, category, spent_on,"
            " owner_id, created_at) VALUES (?,?,?,?,?,?)",
            (e.description, e.amount, e.category,
             e.spent_on.isoformat() if e.spent_on else None,
             e.owner_id, now),
        )
        self.db.conn.commit()
        e.id = cur.lastrowid
        return e

    def list_all(self) -> list[Expense]:
        rows = self.db.conn.execute(
            "SELECT e.*, m.name AS owner_name FROM expenses e"
            " LEFT JOIN family_members m ON m.id = e.owner_id"
            " ORDER BY e.spent_on DESC, e.id DESC")
        return [self._row_to_expense(r) for r in rows]

    def list_in_month(self, year: int, month: int) -> list[Expense]:
        prefix = f"{year:04d}-{month:02d}"
        rows = self.db.conn.execute(
            "SELECT e.*, m.name AS owner_name FROM expenses e"
            " LEFT JOIN family_members m ON m.id = e.owner_id"
            " WHERE e.spent_on LIKE ? ORDER BY e.spent_on DESC",
            (prefix + "%",),
        )
        return [self._row_to_expense(r) for r in rows]

    @staticmethod
    def _row_to_expense(row: sqlite3.Row) -> Expense:
        return Expense(
            id=row["id"],
            description=row["description"],
            amount=row["amount"],
            category=row["category"],
            spent_on=date.fromisoformat(row["spent_on"]) if row["spent_on"] else None,
            owner_id=row["owner_id"],
            owner_name=(row["owner_name"] or "") if "owner_name" in row.keys() else "",
        )


class PriceMemoryRepository:
    """Preisgedaechtnis fuer wiederkehrende Einkaeufe (Modul B)."""

    def __init__(self, db: Database):
        self.db = db

    def remember(self, product: str, price: float,
                 category: str = "sonstiges",
                 seen_on: Optional[date] = None) -> PriceMemory:
        seen = (seen_on or date.today()).isoformat()
        now = datetime.now().isoformat(timespec="seconds")
        self.db.conn.execute(
            "INSERT INTO price_memory (product, last_price, last_seen, "
            "category, created_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(product) DO UPDATE SET "
            "last_price=excluded.last_price, last_seen=excluded.last_seen, "
            "category=excluded.category",
            (product, price, seen, category, now))
        self.db.conn.commit()
        return PriceMemory(product=product, last_price=price,
                           last_seen=seen_on or date.today(),
                           category=category)

    def list_all(self) -> list[PriceMemory]:
        rows = self.db.conn.execute(
            "SELECT * FROM price_memory ORDER BY product")
        return [PriceMemory(
            id=r["id"], product=r["product"], last_price=r["last_price"],
            last_seen=date.fromisoformat(r["last_seen"]) if r["last_seen"] else None,
            category=r["category"]) for r in rows]


# =====================================================================
#  Familie & Haushalt (Modul D)
# =====================================================================
class FamilyRepository:
    def __init__(self, db: Database):
        self.db = db

    # ---- Mitglieder ----------------------------------------------------
    def add_member(self, m: FamilyMember) -> FamilyMember:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO family_members (name, role, birthday, created_at)"
            " VALUES (?,?,?,?)",
            (m.name, m.role,
             m.birthday.isoformat() if m.birthday else None, now),
        )
        self.db.conn.commit()
        m.id = cur.lastrowid
        return m

    def list_members(self) -> list[FamilyMember]:
        rows = self.db.conn.execute("SELECT * FROM family_members ORDER BY id")
        return [self._row_to_member(r) for r in rows]

    def get_member(self, member_id: int) -> Optional[FamilyMember]:
        r = self.db.conn.execute(
            "SELECT * FROM family_members WHERE id=?", (member_id,)
        ).fetchone()
        return self._row_to_member(r) if r else None

    def find_member_by_name(self, name: str) -> Optional[FamilyMember]:
        r = self.db.conn.execute(
            "SELECT * FROM family_members WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone()
        return self._row_to_member(r) if r else None

    @staticmethod
    def _row_to_member(r: sqlite3.Row) -> FamilyMember:
        bday = r["birthday"] if "birthday" in r.keys() else None
        return FamilyMember(
            id=r["id"], name=r["name"], role=r["role"],
            birthday=date.fromisoformat(bday) if bday else None,
        )

    # ---- Wiederkehrende Aufgaben --------------------------------------
    def add_task(self, t: HouseholdTask) -> HouseholdTask:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO household_tasks (title, interval_days, next_due,"
            " current_index, created_at) VALUES (?,?,?,?,?)",
            (t.title, t.interval_days,
             t.next_due.isoformat() if t.next_due else None,
             t.current_index, now),
        )
        task_id = cur.lastrowid
        for position, member_id in enumerate(t.rotation):
            self.db.conn.execute(
                "INSERT INTO task_rotation (task_id, member_id, position)"
                " VALUES (?,?,?)",
                (task_id, member_id, position),
            )
        self.db.conn.commit()
        t.id = task_id
        return t

    def list_tasks(self) -> list[HouseholdTask]:
        tasks: list[HouseholdTask] = []
        for row in self.db.conn.execute(
                "SELECT * FROM household_tasks ORDER BY next_due"):
            rotation = [r["member_id"] for r in self.db.conn.execute(
                "SELECT member_id FROM task_rotation WHERE task_id=?"
                " ORDER BY position", (row["id"],))]
            task = HouseholdTask(
                id=row["id"],
                title=row["title"],
                interval_days=row["interval_days"],
                next_due=(date.fromisoformat(row["next_due"])
                          if row["next_due"] else None),
                rotation=rotation,
                current_index=row["current_index"],
            )
            if rotation:
                member = self.get_member(rotation[task.current_index % len(rotation)])
                task.current_assignee_name = member.name if member else "?"
            tasks.append(task)
        return tasks

    def complete_task(self, task_id: int) -> HouseholdTask:
        row = self.db.conn.execute(
            "SELECT * FROM household_tasks WHERE id=?", (task_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Aufgabe {task_id} existiert nicht")
        rotation = [r["member_id"] for r in self.db.conn.execute(
            "SELECT member_id FROM task_rotation WHERE task_id=? ORDER BY position",
            (task_id,))]
        new_index = ((row["current_index"] + 1) % len(rotation)
                     if rotation else 0)
        current_due = (date.fromisoformat(row["next_due"])
                       if row["next_due"] else date.today())
        base = max(current_due, date.today())
        new_due = base + timedelta(days=row["interval_days"])
        self.db.conn.execute(
            "UPDATE household_tasks SET current_index=?, next_due=? WHERE id=?",
            (new_index, new_due.isoformat(), task_id),
        )
        self.db.conn.commit()
        updated = self.get_task(task_id)
        assert updated is not None    # Zeile existiert garantiert, gerade aktualisiert
        return updated

    def get_task(self, task_id: int) -> Optional[HouseholdTask]:
        for task in self.list_tasks():
            if task.id == task_id:
                return task
        return None

    # ---- Einmalige Auftraege ------------------------------------------
    def add_order(self, o: HouseholdOrder) -> HouseholdOrder:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO household_orders (title, assignee_id, due_date,"
            " description, status, created_at) VALUES (?,?,?,?,?,?)",
            (o.title, o.assignee_id,
             o.due_date.isoformat() if o.due_date else None,
             o.description, o.status, now),
        )
        self.db.conn.commit()
        o.id = cur.lastrowid
        return o

    def list_orders(self, only_open: bool = False) -> list[HouseholdOrder]:
        sql = "SELECT * FROM household_orders"
        if only_open:
            sql += " WHERE status='offen'"
        sql += " ORDER BY due_date"
        orders = []
        for row in self.db.conn.execute(sql):
            order = HouseholdOrder(
                id=row["id"],
                title=row["title"],
                assignee_id=row["assignee_id"],
                due_date=(date.fromisoformat(row["due_date"])
                          if row["due_date"] else None),
                description=row["description"],
                status=row["status"],
            )
            if order.assignee_id:
                member = self.get_member(order.assignee_id)
                order.assignee_name = member.name if member else "?"
            orders.append(order)
        return orders

    def complete_order(self, order_id: int) -> Optional[HouseholdOrder]:
        self.db.conn.execute(
            "UPDATE household_orders SET status='erledigt' WHERE id=?",
            (order_id,))
        self.db.conn.commit()
        for o in self.list_orders():
            if o.id == order_id:
                return o
        return None


class ShoppingRepository:
    """Gemeinsame Einkaufsliste (Modul D)."""

    def __init__(self, db: Database):
        self.db = db

    def add(self, item: ShoppingItem) -> ShoppingItem:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO shopping_items (name, quantity, added_by_id,"
            " bought, created_at) VALUES (?,?,?,?,?)",
            (item.name, item.quantity, item.added_by_id,
             int(bool(item.bought)), now))
        self.db.conn.commit()
        item.id = cur.lastrowid
        return item

    def list(self, include_bought: bool = True) -> list[ShoppingItem]:
        sql = ("SELECT s.*, m.name AS added_by_name FROM shopping_items s"
               " LEFT JOIN family_members m ON m.id = s.added_by_id")
        if not include_bought:
            sql += " WHERE s.bought=0"
        sql += " ORDER BY s.bought ASC, s.id ASC"
        result: list[ShoppingItem] = []
        for row in self.db.conn.execute(sql):
            result.append(ShoppingItem(
                id=row["id"], name=row["name"], quantity=row["quantity"],
                added_by_id=row["added_by_id"],
                bought=bool(row["bought"]),
                added_by_name=(row["added_by_name"] or "")
                              if "added_by_name" in row.keys() else "",
            ))
        return result

    def mark_bought(self, item_id: int, bought: bool = True) -> None:
        self.db.conn.execute(
            "UPDATE shopping_items SET bought=? WHERE id=?",
            (int(bought), item_id))
        self.db.conn.commit()

    def remove(self, item_id: int) -> None:
        self.db.conn.execute(
            "DELETE FROM shopping_items WHERE id=?", (item_id,))
        self.db.conn.commit()


# =====================================================================
#  Vorschlaege (Posteingang)
# =====================================================================
class ProposalRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, p: Proposal) -> Proposal:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO proposals (source, summary, target_capability,"
            " payload, status, created_at) VALUES (?,?,?,?,?,?)",
            (p.source, p.summary, p.target_capability,
             json.dumps(p.payload, ensure_ascii=False), p.status, now),
        )
        self.db.conn.commit()
        p.id = cur.lastrowid
        return p

    def list(self, status: Optional[str] = None) -> list[Proposal]:
        sql = "SELECT * FROM proposals"
        params: tuple = ()
        if status:
            sql += " WHERE status=?"
            params = (status,)
        sql += " ORDER BY id DESC"
        return [self._row_to_proposal(r)
                for r in self.db.conn.execute(sql, params)]

    def get(self, proposal_id: int) -> Optional[Proposal]:
        r = self.db.conn.execute(
            "SELECT * FROM proposals WHERE id=?", (proposal_id,)
        ).fetchone()
        return self._row_to_proposal(r) if r else None

    def set_status(self, proposal_id: int, status: str) -> None:
        self.db.conn.execute(
            "UPDATE proposals SET status=? WHERE id=?", (status, proposal_id))
        self.db.conn.commit()

    @staticmethod
    def _row_to_proposal(row: sqlite3.Row) -> Proposal:
        return Proposal(
            id=row["id"],
            source=row["source"],
            summary=row["summary"],
            target_capability=row["target_capability"],
            payload=json.loads(row["payload"]) if row["payload"] else {},
            status=row["status"],
        )


# =====================================================================
#  Termine & Kalender (Modul C)
# =====================================================================
class CalendarRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, e: CalendarEvent) -> CalendarEvent:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO calendar_events (title, due_date, category,"
            " description, recurrence_days, person_id, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (e.title, e.due_date.isoformat(), e.category, e.description,
             e.recurrence_days, e.person_id, now))
        self.db.conn.commit()
        e.id = cur.lastrowid
        return e

    def list_all(self) -> list[CalendarEvent]:
        rows = self.db.conn.execute(
            "SELECT c.*, m.name AS person_name FROM calendar_events c"
            " LEFT JOIN family_members m ON m.id = c.person_id"
            " ORDER BY c.due_date")
        return [self._row_to_event(r) for r in rows]

    def list_upcoming(self, horizon_days: int = 90) -> list[CalendarEvent]:
        # Liefert alle (auch ueberfaellige) bis horizon_days in der Zukunft.
        events: list[CalendarEvent] = []
        today = date.today()
        for e in self.list_all():
            next_occurrence = self._next_occurrence(e, today)
            if next_occurrence is None:
                continue
            days = (next_occurrence - today).days
            if days <= horizon_days:
                e.due_date = next_occurrence    # auf naechstes Auftreten setzen
                events.append(e)
        events.sort(key=lambda x: x.due_date)
        return events

    @staticmethod
    def _next_occurrence(e: CalendarEvent, today: date) -> Optional[date]:
        if not e.recurrence_days:
            return e.due_date if e.due_date >= today - timedelta(days=30) else None
        d = e.due_date
        while d < today:
            d = d + timedelta(days=e.recurrence_days)
        return d

    def delete(self, event_id: int) -> None:
        self.db.conn.execute(
            "DELETE FROM calendar_events WHERE id=?", (event_id,))
        self.db.conn.commit()

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> CalendarEvent:
        return CalendarEvent(
            id=row["id"], title=row["title"],
            due_date=date.fromisoformat(row["due_date"]),
            category=row["category"], description=row["description"],
            recurrence_days=row["recurrence_days"],
            person_id=row["person_id"],
            person_name=(row["person_name"] or "")
                          if "person_name" in row.keys() else "",
        )


# =====================================================================
#  Soziale Pflege (Modul E)
# =====================================================================
class SocialRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, c: SocialContact) -> SocialContact:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO social_contacts (name, relation, cadence_days,"
            " last_contacted, notes, created_at) VALUES (?,?,?,?,?,?)",
            (c.name, c.relation, c.cadence_days,
             c.last_contacted.isoformat() if c.last_contacted else None,
             c.notes, now))
        self.db.conn.commit()
        c.id = cur.lastrowid
        return c

    def list_all(self) -> list[SocialContact]:
        rows = self.db.conn.execute(
            "SELECT * FROM social_contacts ORDER BY name")
        return [self._row_to_contact(r) for r in rows]

    def get(self, contact_id: int) -> Optional[SocialContact]:
        r = self.db.conn.execute(
            "SELECT * FROM social_contacts WHERE id=?", (contact_id,)
        ).fetchone()
        return self._row_to_contact(r) if r else None

    def mark_contacted(self, contact_id: int,
                       contacted_on: Optional[date] = None) -> None:
        self.db.conn.execute(
            "UPDATE social_contacts SET last_contacted=? WHERE id=?",
            ((contacted_on or date.today()).isoformat(), contact_id))
        self.db.conn.commit()

    @staticmethod
    def _row_to_contact(row: sqlite3.Row) -> SocialContact:
        last = row["last_contacted"]
        return SocialContact(
            id=row["id"], name=row["name"], relation=row["relation"],
            cadence_days=row["cadence_days"],
            last_contacted=date.fromisoformat(last) if last else None,
            notes=row["notes"],
        )


# =====================================================================
#  Assistenten-Log
# =====================================================================
class AssistantLogRepository:
    def __init__(self, db: Database):
        self.db = db

    def append(self, role: str, content: str) -> AssistantLogEntry:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO assistant_log (role, content, created_at)"
            " VALUES (?,?,?)", (role, content, now))
        self.db.conn.commit()
        return AssistantLogEntry(id=cur.lastrowid, role=role, content=content)

    def tail(self, limit: int = 20) -> list[AssistantLogEntry]:
        rows = self.db.conn.execute(
            "SELECT * FROM assistant_log ORDER BY id DESC LIMIT ?",
            (limit,))
        out: list[AssistantLogEntry] = []
        for r in rows:
            out.append(AssistantLogEntry(
                id=r["id"], role=r["role"], content=r["content"]))
        return list(reversed(out))
