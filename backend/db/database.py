"""Database connection helpers and initialization."""

import logging
import os
import sqlite3
from contextlib import contextmanager

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Extract the file path from the DATABASE_URL (strip "sqlite:///")
DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

# Ensure the directory for the database file exists
db_dir = os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else "."
os.makedirs(db_dir, exist_ok=True)
logger.info("Database directory ensured at %s", db_dir)


def get_connection() -> sqlite3.Connection:
    """Create and return a new SQLite connection with row factory."""
    logger.trace("Opening database connection to %s", DB_PATH)
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
        logger.trace("Database transaction committed")
    except Exception:
        logger.error("Database transaction rolled back", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()
        logger.trace("Database connection closed")


def init_db() -> None:
    """Initialize the database by creating all tables."""
    logger.info("Initializing database schema")
    from backend.db import schema  # noqa: F401 – triggers table creation
    schema.create_tables()
