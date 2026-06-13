-- Generiert aus dem echten SQLite-Schema (database.py)
-- via tools/gen_ai_studio_contracts.py. Nicht haendisch editieren.

CREATE TABLE app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT,
    updated_at TEXT
);

CREATE TABLE assistant_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT,
    content    TEXT,
    created_at TEXT
);

CREATE TABLE audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            action      TEXT NOT NULL,
            entity_type TEXT,
            entity_id   INTEGER,
            details     TEXT,
            actor       TEXT,
            created_at  TEXT
        );

CREATE TABLE calendar_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    due_date        TEXT NOT NULL,
    category        TEXT DEFAULT 'termin',
    description     TEXT DEFAULT '',
    recurrence_days INTEGER,
    person_id       INTEGER,
    created_at      TEXT, deleted_at TEXT,
    FOREIGN KEY (person_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE contracts (
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
    updated_at           TEXT, deleted_at TEXT,
    FOREIGN KEY (owner_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE day_entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    day        TEXT NOT NULL UNIQUE,
    level      INTEGER NOT NULL,
    note       TEXT DEFAULT '',
    created_at TEXT
);

CREATE TABLE expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount      REAL NOT NULL,
    category    TEXT DEFAULT 'sonstiges',
    spent_on    TEXT,
    owner_id    INTEGER,
    created_at  TEXT, deleted_at TEXT,
    FOREIGN KEY (owner_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE family_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    role       TEXT DEFAULT 'erwachsen',
    birthday   TEXT,
    created_at TEXT
, deleted_at TEXT);

CREATE TABLE household_orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    assignee_id INTEGER,
    due_date    TEXT,
    description TEXT DEFAULT '',
    status      TEXT DEFAULT 'offen',
    priority    TEXT DEFAULT 'normal',
    category    TEXT DEFAULT '',
    created_at  TEXT, deleted_at TEXT,
    FOREIGN KEY (assignee_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE household_tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    interval_days INTEGER DEFAULT 7,
    next_due      TEXT,
    current_index INTEGER DEFAULT 0,
    created_at    TEXT
);

CREATE TABLE module_states (
    module_id  TEXT PRIMARY KEY,
    enabled    INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT
);

CREATE TABLE note_attachments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            note_id     INTEGER NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id   INTEGER NOT NULL,
            created_at  TEXT,
            FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
        );

CREATE TABLE notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    content     TEXT DEFAULT '',
    entity_type TEXT,
    entity_id   INTEGER,
    created_at  TEXT,
    updated_at  TEXT
, deleted_at TEXT);

CREATE TABLE price_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    old_cost    REAL,
    new_cost    REAL,
    changed_at  TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
);

CREATE TABLE price_memory (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product    TEXT NOT NULL UNIQUE,
    last_price REAL,
    last_seen  TEXT,
    category   TEXT DEFAULT 'sonstiges',
    created_at TEXT
);

CREATE TABLE proposals (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT,
    summary           TEXT,
    target_capability TEXT,
    payload           TEXT,
    status            TEXT DEFAULT 'offen',
    created_at        TEXT
);

CREATE TABLE shopping_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    quantity    TEXT DEFAULT '',
    added_by_id INTEGER,
    bought      INTEGER DEFAULT 0,
    created_at  TEXT,
    FOREIGN KEY (added_by_id) REFERENCES family_members(id) ON DELETE SET NULL
);

CREATE TABLE social_contacts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    relation       TEXT DEFAULT '',
    cadence_days   INTEGER DEFAULT 30,
    last_contacted TEXT,
    notes          TEXT DEFAULT '',
    created_at     TEXT
, deleted_at TEXT);

CREATE TABLE task_rotation (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id   INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    position  INTEGER NOT NULL,
    FOREIGN KEY (task_id)   REFERENCES household_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES family_members(id)  ON DELETE CASCADE
);

CREATE TABLE task_templates (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            interval_days INTEGER NOT NULL DEFAULT 7,
            description   TEXT DEFAULT '',
            created_at    TEXT
        );

CREATE INDEX idx_note_attachments_entity
            ON note_attachments(entity_type, entity_id);

CREATE INDEX idx_note_attachments_note
            ON note_attachments(note_id);

CREATE INDEX idx_notes_entity
    ON notes(entity_type, entity_id);
