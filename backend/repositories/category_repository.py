"""
Repository layer for Category persistence.
All SQL for the `categories` table lives here.
"""
import sqlite3
from typing import Optional
from datetime import datetime, timezone

from backend.models.category import Category


class CategoryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, category_id: int) -> Optional[Category]:
        row = self._conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        return Category.from_row(row) if row else None

    def get_by_name(self, name: str) -> Optional[Category]:
        row = self._conn.execute(
            "SELECT * FROM categories WHERE name = ?", (name,)
        ).fetchone()
        return Category.from_row(row) if row else None

    def list_all(self) -> list[Category]:
        rows = self._conn.execute(
            "SELECT * FROM categories ORDER BY name"
        ).fetchall()
        return [Category.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        description: Optional[str],
        created_by: int,
    ) -> Category:
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO categories (name, description, created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, description, created_by, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        updated_by: Optional[int] = None,
    ) -> Optional[Category]:
        fields: dict = {}
        if name is not None:
            fields["name"] = name
        if description is not None:
            fields["description"] = description
        if updated_by is not None:
            fields["updated_by"] = updated_by

        if not fields:
            return self.get_by_id(category_id)

        fields["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [category_id]
        self._conn.execute(
            f"UPDATE categories SET {set_clause} WHERE id = ?", values
        )
        return self.get_by_id(category_id)

    def delete(self, category_id: int) -> bool:
        """Delete a category. Will fail if items reference this category (ON DELETE RESTRICT)."""
        cursor = self._conn.execute(
            "DELETE FROM categories WHERE id = ?", (category_id,)
        )
        return cursor.rowcount > 0