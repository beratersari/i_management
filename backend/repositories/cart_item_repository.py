"""
Repository layer for CartItem persistence.
All SQL for the `cart_items` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from backend.models.cart_item import CartItem


class CartItemRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, cart_item_id: int) -> Optional[CartItem]:
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE id = ?",
            (cart_item_id,),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    def get_by_cart_item(self, cart_id: int, item_id: int) -> Optional[CartItem]:
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?",
            (cart_id, item_id),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    def list_by_cart(self, cart_id: int) -> list[CartItem]:
        rows = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? ORDER BY id",
            (cart_id,),
        ).fetchall()
        return [CartItem.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        cart_id: int,
        item_id: int,
        quantity: float,
        created_by: int,
    ) -> CartItem:
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO cart_items (
                cart_id, item_id, quantity, created_by, updated_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (cart_id, item_id, quantity, created_by, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update_quantity(
        self,
        cart_item_id: int,
        quantity: float,
        updated_by: int,
    ) -> Optional[CartItem]:
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE cart_items
               SET quantity = ?, updated_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (quantity, updated_by, now, cart_item_id),
        )
        return self.get_by_id(cart_item_id)

    def delete(self, cart_item_id: int) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE id = ?",
            (cart_item_id,),
        )
        return cursor.rowcount > 0

    def clear_cart(self, cart_id: int) -> int:
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE cart_id = ?",
            (cart_id,),
        )
        return cursor.rowcount
