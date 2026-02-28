"""
Repository layer for CartItem persistence.
All SQL for the `cart_items` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.cart_item import CartItem

logger = logging.getLogger(__name__)


class CartItemRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing CartItemRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, cart_item_id: int) -> Optional[CartItem]:
        logger.trace("Fetching cart item id=%s", cart_item_id)
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE id = ?",
            (cart_item_id,),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    def get_by_cart_item(self, cart_id: int, item_id: int) -> Optional[CartItem]:
        logger.trace("Fetching cart item cart_id=%s item_id=%s", cart_id, item_id)
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?",
            (cart_id, item_id),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    def list_by_cart(self, cart_id: int) -> list[CartItem]:
        logger.trace("Listing cart items cart_id=%s", cart_id)
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
        logger.info("Creating cart item cart_id=%s item_id=%s", cart_id, item_id)
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
        logger.info("Updating cart item quantity id=%s", cart_item_id)
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
        logger.info("Deleting cart item id=%s", cart_item_id)
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE id = ?",
            (cart_item_id,),
        )
        logger.info("Cart item delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0

    def clear_cart(self, cart_id: int) -> int:
        logger.info("Clearing cart items cart_id=%s", cart_id)
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE cart_id = ?",
            (cart_id,),
        )
        logger.info("Cleared %s cart items for cart_id=%s", cursor.rowcount, cart_id)
        return cursor.rowcount
