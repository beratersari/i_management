"""
Repository layer for Category persistence.
All SQL for the `categories` table lives here.
"""
import sqlite3
from typing import Optional
from datetime import datetime, timezone
import logging

from backend.models.category import Category
from backend.core.logging_config import log_db_timing

logger = logging.getLogger(__name__)


class CategoryRepository:
    """Data access layer for category records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Store the database connection for query execution."""
        logger.trace("Initializing CategoryRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @log_db_timing
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Return a category by id or None if missing."""
        logger.trace("Fetching category id=%s", category_id)
        row = self._conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        return Category.from_row(row) if row else None

    @log_db_timing
    def get_by_name(self, name: str) -> Optional[Category]:
        """Return a category by name or None if missing."""
        logger.trace("Fetching category by name=%s", name)
        row = self._conn.execute(
            "SELECT * FROM categories WHERE name = ?", (name,)
        ).fetchone()
        return Category.from_row(row) if row else None

    @log_db_timing
    def list_all(self) -> list[Category]:
        """Return all categories ordered by sort order and name."""
        logger.trace("Listing categories")
        rows = self._conn.execute(
            "SELECT * FROM categories ORDER BY sort_order, name"
        ).fetchall()
        return [Category.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @log_db_timing
    def create(
        self,
        name: str,
        description: Optional[str],
        created_by: int,
    ) -> Category:
        """Insert a new category and return the created row."""
        logger.info("Creating category record name=%s", name)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO categories (name, description, created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, description, created_by, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    @log_db_timing
    def update(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
        updated_by: Optional[int] = None,
    ) -> Optional[Category]:
        """Update category fields and return the updated row."""
        fields: dict = {}
        if name is not None:
            fields["name"] = name
        if description is not None:
            fields["description"] = description
        if sort_order is not None:
            fields["sort_order"] = sort_order
        if updated_by is not None:
            fields["updated_by"] = updated_by

        if not fields:
            logger.trace("No category fields to update id=%s", category_id)
            return self.get_by_id(category_id)

        logger.info("Updating category record id=%s", category_id)
        fields["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [category_id]
        self._conn.execute(
            f"UPDATE categories SET {set_clause} WHERE id = ?", values
        )
        return self.get_by_id(category_id)

    @log_db_timing
    def delete(self, category_id: int) -> bool:
        """Delete a category and return True if removed."""
        logger.info("Deleting category record id=%s", category_id)
        cursor = self._conn.execute(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        logger.info("Category delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0