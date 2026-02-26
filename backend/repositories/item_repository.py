"""
Repository layer for Item persistence.
All SQL for the `items` table lives here.
"""
import sqlite3
from typing import Optional
from datetime import datetime, timezone

from backend.models.item import Item


class ItemRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, item_id: int) -> Optional[Item]:
        row = self._conn.execute(
            "SELECT * FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        return Item.from_row(row) if row else None

    def get_by_sku(self, sku: str) -> Optional[Item]:
        row = self._conn.execute(
            "SELECT * FROM items WHERE sku = ?", (sku,)
        ).fetchone()
        return Item.from_row(row) if row else None

    def list_all(self, category_id: Optional[int] = None) -> list[Item]:
        if category_id:
            rows = self._conn.execute(
                "SELECT * FROM items WHERE category_id = ? ORDER BY name",
                (category_id,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM items ORDER BY name"
            ).fetchall()
        return [Item.from_row(r) for r in rows]

    def search_by_name(self, query: str) -> list[Item]:
        """Search items by name (case-insensitive)."""
        rows = self._conn.execute(
            "SELECT * FROM items WHERE name LIKE ? ORDER BY name",
            (f"%{query}%",)
        ).fetchall()
        return [Item.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        category_id: int,
        name: str,
        description: Optional[str],
        sku: Optional[str],
        barcode: Optional[str],
        image_url: Optional[str],
        unit_price: float,
        unit_type: str,
        tax_rate: float,
        discount_rate: float,
        created_by: int,
    ) -> Item:
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO items (
                category_id, name, description, sku, barcode, image_url,
                unit_price, unit_type, tax_rate, discount_rate,
                created_by, updated_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                category_id, name, description, sku, barcode, image_url,
                unit_price, unit_type, tax_rate, discount_rate,
                created_by, created_by, now, now,
            ),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update(self, item_id: int, **fields) -> Optional[Item]:
        """Update arbitrary fields on an item."""
        if not fields:
            return self.get_by_id(item_id)

        fields["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [item_id]
        self._conn.execute(
            f"UPDATE items SET {set_clause} WHERE id = ?", values
        )
        return self.get_by_id(item_id)

    def delete(self, item_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM items WHERE id = ?", (item_id,)
        )
        return cursor.rowcount > 0