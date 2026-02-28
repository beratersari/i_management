"""
SQL DDL statements for all application tables.
Tables are created in dependency order so foreign keys resolve correctly.

Migration helpers run ALTER TABLE only when a column does not yet exist,
making them safe to call on every startup (idempotent).
"""
import logging

from backend.db.database import get_connection

logger = logging.getLogger(__name__)

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
    sort_order  INTEGER NOT NULL DEFAULT 0,
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

CREATE_MENU_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS menu_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id       INTEGER NOT NULL UNIQUE REFERENCES items(id) ON DELETE CASCADE,
    display_name  TEXT    NOT NULL,
    description   TEXT,
    allergens     TEXT,
    created_by    INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
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

CREATE_CARTS_TABLE = """
CREATE TABLE IF NOT EXISTS carts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    desk_number  TEXT    UNIQUE,
    created_by   INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by   INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_CART_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS cart_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id     INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
    quantity    REAL    NOT NULL DEFAULT 0.0
                        CHECK(quantity >= 0),
    created_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by  INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (cart_id, item_id)
);
"""

CREATE_DAILY_ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS daily_accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_date    TEXT    NOT NULL UNIQUE,
    subtotal        REAL    NOT NULL DEFAULT 0.0,
    discount_total  REAL    NOT NULL DEFAULT 0.0,
    tax_total       REAL    NOT NULL DEFAULT 0.0,
    total           REAL    NOT NULL DEFAULT 0.0,
    carts_count     INTEGER NOT NULL DEFAULT 0,
    items_count     INTEGER NOT NULL DEFAULT 0,
    is_closed       INTEGER NOT NULL DEFAULT 0,
    closed_at       TEXT,
    closed_by       INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_DAILY_ACCOUNT_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS daily_account_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id      INTEGER NOT NULL REFERENCES daily_accounts(id) ON DELETE CASCADE,
    item_id         INTEGER NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
    item_name       TEXT    NOT NULL,
    sku             TEXT,
    quantity        REAL    NOT NULL DEFAULT 0.0,
    unit_price      REAL    NOT NULL DEFAULT 0.0,
    discount_rate   REAL    NOT NULL DEFAULT 0.0,
    tax_rate        REAL    NOT NULL DEFAULT 0.0,
    line_subtotal   REAL    NOT NULL DEFAULT 0.0,
    line_discount   REAL    NOT NULL DEFAULT 0.0,
    line_tax        REAL    NOT NULL DEFAULT 0.0,
    line_total      REAL    NOT NULL DEFAULT 0.0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_TIME_ENTRIES_TABLE = """
CREATE TABLE IF NOT EXISTS time_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    work_date       TEXT    NOT NULL,
    start_hour      TEXT    NOT NULL,
    end_hour        TEXT    NOT NULL,
    hours_worked    REAL    NOT NULL DEFAULT 0.0,
    notes           TEXT,
    status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending', 'accepted', 'rejected')),
    reviewed_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at     TEXT,
    rejection_reason TEXT,
    created_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    updated_by      INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# ---------------------------------------------------------------------------
# Incremental migrations (idempotent – safe to run every startup)
# ---------------------------------------------------------------------------

MIGRATIONS = [
    # Add soft-delete columns if they were not in the original schema
    ("users", "is_deleted",      "ALTER TABLE users ADD COLUMN is_deleted      INTEGER NOT NULL DEFAULT 0"),
    ("users", "deleted_at",      "ALTER TABLE users ADD COLUMN deleted_at      TEXT"),
    ("categories", "sort_order", "ALTER TABLE categories ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"),
    ("menu_items", "display_name", "ALTER TABLE menu_items ADD COLUMN display_name TEXT NOT NULL DEFAULT ''"),
    ("menu_items", "description", "ALTER TABLE menu_items ADD COLUMN description TEXT"),
    ("menu_items", "allergens", "ALTER TABLE menu_items ADD COLUMN allergens TEXT"),
    ("carts", "desk_number", "ALTER TABLE carts ADD COLUMN desk_number TEXT"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_REFRESH_TOKENS_TABLE,
    CREATE_CATEGORIES_TABLE,
    CREATE_ITEMS_TABLE,
    CREATE_MENU_ITEMS_TABLE,
    CREATE_STOCK_TABLE,
    CREATE_CARTS_TABLE,
    CREATE_CART_ITEMS_TABLE,
    CREATE_DAILY_ACCOUNTS_TABLE,
    CREATE_DAILY_ACCOUNT_ITEMS_TABLE,
    CREATE_TIME_ENTRIES_TABLE,
]


def _column_exists(conn, table: str, column: str) -> bool:
    logger.trace("Checking column existence table=%s column=%s", table, column)
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def create_tables() -> None:
    """Create all tables and apply incremental migrations."""
    logger.info("Creating database tables and applying migrations")
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Create tables (IF NOT EXISTS – safe on every restart)
        for ddl in ALL_TABLES:
            cursor.execute(ddl)

        # 2. Run migrations only when the column is missing
        for table, column, alter_sql in MIGRATIONS:
            if not _column_exists(conn, table, column):
                logger.warning("Applying migration for %s.%s", table, column)
                cursor.execute(alter_sql)

        conn.commit()
        logger.info("Database schema ready")
    finally:
        conn.close()
