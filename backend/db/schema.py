"""
SQL DDL statements for all application tables.
Tables are created in dependency order so foreign keys resolve correctly.

Migration helpers run ALTER TABLE only when a column does not yet exist,
making them safe to call on every startup (idempotent).
"""
from backend.db.database import get_connection

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    email             TEXT    NOT NULL UNIQUE,
    username          TEXT    NOT NULL UNIQUE,
    full_name         TEXT,
    hashed_password   TEXT    NOT NULL,
    role              TEXT    NOT NULL DEFAULT 'employee'
                              CHECK(role IN ('admin', 'market_owner', 'employee')),
    is_active         INTEGER NOT NULL DEFAULT 1,
    is_deleted        INTEGER NOT NULL DEFAULT 0,
    deleted_at        TEXT,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_REFRESH_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token       TEXT    NOT NULL UNIQUE,
    expires_at  TEXT    NOT NULL,
    revoked     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    created_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id     INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name            TEXT    NOT NULL,
    description     TEXT,
    sku             TEXT    UNIQUE,
    barcode         TEXT,
    image_url       TEXT,
    unit_price      REAL    NOT NULL DEFAULT 0.0,
    unit_type       TEXT    NOT NULL DEFAULT 'piece',
    tax_rate        REAL    NOT NULL DEFAULT 0.0,
    discount_rate   REAL    NOT NULL DEFAULT 0.0,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_STOCK_TABLE = """
CREATE TABLE IF NOT EXISTS stock_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL UNIQUE REFERENCES items(id) ON DELETE CASCADE,
    quantity    REAL    NOT NULL DEFAULT 0.0
                        CHECK(quantity >= 0),
    created_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# ---------------------------------------------------------------------------
# Incremental migrations (idempotent – safe to run every startup)
# ---------------------------------------------------------------------------

MIGRATIONS = [
    # Add soft-delete columns if they were not in the original schema
    ("users", "is_deleted",      "ALTER TABLE users ADD COLUMN is_deleted      INTEGER NOT NULL DEFAULT 0"),
    ("users", "deleted_at",      "ALTER TABLE users ADD COLUMN deleted_at      TEXT"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_REFRESH_TOKENS_TABLE,
    CREATE_CATEGORIES_TABLE,
    CREATE_ITEMS_TABLE,
    CREATE_STOCK_TABLE,
]


def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def create_tables() -> None:
    """Create all tables and apply incremental migrations."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Create tables (IF NOT EXISTS – safe on every restart)
        for ddl in ALL_TABLES:
            cursor.execute(ddl)

        # 2. Run migrations only when the column is missing
        for table, column, alter_sql in MIGRATIONS:
            if not _column_exists(conn, table, column):
                cursor.execute(alter_sql)

        conn.commit()
    finally:
        conn.close()
