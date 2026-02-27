"""
Repository layer for Cart persistence.
All SQL for the `carts` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from backend.models.cart import Cart


class CartRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, cart_id: int) -> Optional[Cart]:
        row = self._conn.execute(
            "SELECT * FROM carts WHERE id = ?",
            (cart_id,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, created_by: int) -> Cart:
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO carts (created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (created_by, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def touch(self, cart_id: int, updated_by: int) -> Optional[Cart]:
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE carts
               SET updated_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (updated_by, now, cart_id),
        )
        return self.get_by_id(cart_id)
