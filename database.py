"""
Datenschicht - SQLite.

Diese Schicht kennt nur Speicherung. Sie weiss nichts vom KI-Assistenten.
Der Zugriff laeuft ueber das Repository, das Domaenenobjekte zurueckgibt.

Hinweis Datenschutz: In Produktion sollte die DB mit SQLCipher
verschluesselt werden - dafuer 'pysqlcipher3' statt 'sqlite3' nutzen.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from models import (Contract, Deadline, Expense, FamilyMember,
                    HouseholdOrder, HouseholdTask, Proposal)

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
    created_at           TEXT,
    updated_at           TEXT
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
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS family_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    role       TEXT DEFAULT 'erwachsen',
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

CREATE TABLE IF NOT EXISTS proposals (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT,
    summary           TEXT,
    target_capability TEXT,
    payload           TEXT,
    status            TEXT DEFAULT 'offen',
    created_at        TEXT
);

CREATE TABLE IF NOT EXISTS assistant_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    role      TEXT,
    content   TEXT
);
"""


class Database:
    """Duenne Wrapper-Klasse um die SQLite-Verbindung."""

    def __init__(self, path: str = "alltagshelfer.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


class ContractRepository:
    """Repository = einzige Tuer zu den Vertragsdaten."""

    def __init__(self, db: Database):
        self.db = db

    # ---- Schreiben -----------------------------------------------------
    def add(self, c: Contract) -> Contract:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            """INSERT INTO contracts
               (name, category, provider, customer_number, start_date,
                minimum_term_months, notice_period_months, auto_renew_months,
                monthly_cost, currency, notes, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (c.name, c.category, c.provider, c.customer_number,
             c.start_date.isoformat() if c.start_date else None,
             c.minimum_term_months, c.notice_period_months,
             c.auto_renew_months, c.monthly_cost, c.currency,
             c.notes, c.status, now, now),
        )
        self.db.conn.commit()
        c.id = cur.lastrowid
        return c

    def update_cost(self, contract_id: int, new_cost: float) -> None:
        """Aendert den Preis und schreibt zugleich in die Preis-Historie."""
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

    # ---- Lesen ---------------------------------------------------------
    def get(self, contract_id: int) -> Optional[Contract]:
        row = self.db.conn.execute(
            "SELECT * FROM contracts WHERE id=?", (contract_id,)
        ).fetchone()
        return self._row_to_contract(row) if row else None

    def list_all(self, only_active: bool = True) -> list[Contract]:
        sql = "SELECT * FROM contracts"
        if only_active:
            sql += " WHERE status='active'"
        sql += " ORDER BY name"
        return [self._row_to_contract(r) for r in self.db.conn.execute(sql)]

    def price_changes(self, contract_id: int) -> list[dict]:
        rows = self.db.conn.execute(
            "SELECT old_cost, new_cost, changed_at FROM price_history"
            " WHERE contract_id=? ORDER BY changed_at DESC",
            (contract_id,),
        )
        return [dict(r) for r in rows]

    # ---- Hilfsfunktion -------------------------------------------------
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
        )


class ExpenseRepository:
    """Repository fuer einmalige Ausgaben (Modul B)."""

    def __init__(self, db: Database):
        self.db = db

    def add(self, e: Expense) -> Expense:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO expenses (description, amount, category, spent_on, created_at)"
            " VALUES (?,?,?,?,?)",
            (e.description, e.amount, e.category,
             e.spent_on.isoformat() if e.spent_on else None, now),
        )
        self.db.conn.commit()
        e.id = cur.lastrowid
        return e

    def list_all(self) -> list[Expense]:
        rows = self.db.conn.execute(
            "SELECT * FROM expenses ORDER BY spent_on DESC, id DESC"
        )
        return [self._row_to_expense(r) for r in rows]

    def list_in_month(self, year: int, month: int) -> list[Expense]:
        prefix = f"{year:04d}-{month:02d}"
        rows = self.db.conn.execute(
            "SELECT * FROM expenses WHERE spent_on LIKE ? ORDER BY spent_on DESC",
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
        )


class FamilyRepository:
    """Repository fuer Haushaltsmitglieder und Aufgaben (Modul D)."""

    def __init__(self, db: Database):
        self.db = db

    # ---- Mitglieder ----------------------------------------------------
    def add_member(self, m: FamilyMember) -> FamilyMember:
        now = datetime.now().isoformat(timespec="seconds")
        cur = self.db.conn.execute(
            "INSERT INTO family_members (name, role, created_at) VALUES (?,?,?)",
            (m.name, m.role, now),
        )
        self.db.conn.commit()
        m.id = cur.lastrowid
        return m

    def list_members(self) -> list[FamilyMember]:
        rows = self.db.conn.execute("SELECT * FROM family_members ORDER BY id")
        return [FamilyMember(id=r["id"], name=r["name"], role=r["role"])
                for r in rows]

    def get_member(self, member_id: int) -> Optional[FamilyMember]:
        r = self.db.conn.execute(
            "SELECT * FROM family_members WHERE id=?", (member_id,)
        ).fetchone()
        return FamilyMember(id=r["id"], name=r["name"], role=r["role"]) if r else None

    def find_member_by_name(self, name: str) -> Optional[FamilyMember]:
        r = self.db.conn.execute(
            "SELECT * FROM family_members WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone()
        return FamilyMember(id=r["id"], name=r["name"], role=r["role"]) if r else None

    # ---- Aufgaben ------------------------------------------------------
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
        """Hakt eine Aufgabe ab: Rotation weiterruecken, neu terminieren."""
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
        return self.get_task(task_id)

    def get_task(self, task_id: int) -> Optional[HouseholdTask]:
        for task in self.list_tasks():
            if task.id == task_id:
                return task
        return None

    # ---- Auftraege (einmalig, gezielt zugewiesen) ----------------------
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


class ProposalRepository:
    """Repository fuer die zentrale Vorschlags-Ablage."""

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
