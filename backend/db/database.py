import sqlite3
import os
from contextlib import contextmanager
from backend.core.config import settings

# Extract the file path from the DATABASE_URL (strip "sqlite:///")
DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

# Ensure the directory for the database file exists
os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Create and return a new SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager that yields a database connection and auto-commits/rolls back."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    from backend.db import schema  # noqa: F401 – triggers table creation
    schema.create_tables()
