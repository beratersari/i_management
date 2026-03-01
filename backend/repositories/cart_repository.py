"""
Repository layer for Cart persistence.
All SQL for the `carts` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.cart import Cart
from backend.models.cart_item import CartItem

logger = logging.getLogger(__name__)


class CartRepository:
    """Data access layer for cart records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Store the database connection for query execution."""
        logger.trace("Initializing CartRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, cart_id: int) -> Optional[Cart]:
        """Return a cart by its id or None if missing."""
        logger.trace("Fetching cart id=%s", cart_id)
        row = self._conn.execute(
            "SELECT * FROM carts WHERE id = ?",
            (cart_id,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    def get_by_desk_number(self, desk_number: str) -> Optional[Cart]:
        """Return a cart by its desk number, if assigned."""
        logger.trace("Fetching cart by desk_number=%s", desk_number)
        row = self._conn.execute(
            "SELECT * FROM carts WHERE desk_number = ?",
            (desk_number,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    def list_with_desk_number(self) -> list[Cart]:
        """List all carts that have a desk number assigned."""
        logger.trace("Listing carts with desk_number")
        rows = self._conn.execute(
            "SELECT * FROM carts WHERE desk_number IS NOT NULL ORDER BY desk_number"
        ).fetchall()
        return [Cart.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, created_by: int) -> Cart:
        """Insert a new cart and return the created record."""
        logger.info("Creating cart record created_by=%s", created_by)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO carts (created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (created_by, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update_desk_number(self, cart_id: int, desk_number: str | None, updated_by: int) -> Optional[Cart]:
        """Update a cart's desk number and return the updated row."""
        logger.info("Updating cart id=%s desk_number=%s", cart_id, desk_number)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE carts
               SET desk_number = ?, updated_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (desk_number, updated_by, now, cart_id),
        )
        return self.get_by_id(cart_id)

    # ------------------------------------------------------------------
    # Cart items
    # ------------------------------------------------------------------

    def get_cart_item_by_id(self, cart_item_id: int) -> Optional[CartItem]:
        """Return a cart item by its id or None if missing."""
        logger.trace("Fetching cart item id=%s", cart_item_id)
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE id = ?",
            (cart_item_id,),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    def get_cart_item_by_cart_and_item(self, cart_id: int, item_id: int) -> Optional[CartItem]:
        """Return a cart item for the given cart and item ids."""
        logger.trace("Fetching cart item cart_id=%s item_id=%s", cart_id, item_id)
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?",
            (cart_id, item_id),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    def list_cart_items_by_cart(self, cart_id: int) -> list[CartItem]:
        """Return all cart items for a given cart."""
        logger.trace("Listing cart items cart_id=%s", cart_id)
        rows = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? ORDER BY id",
            (cart_id,),
        ).fetchall()
        return [CartItem.from_row(row) for row in rows]

    def create_cart_item(
        self,
        cart_id: int,
        item_id: int,
        quantity: float,
        created_by: int,
    ) -> CartItem:
        """Insert a new cart item and return it."""
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
        return self.get_cart_item_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update_cart_item_quantity(
        self,
        cart_item_id: int,
        quantity: float,
        updated_by: int,
    ) -> Optional[CartItem]:
        """Update the quantity for a cart item and return the new row."""
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
        return self.get_cart_item_by_id(cart_item_id)

    def delete_cart_item(self, cart_item_id: int) -> bool:
        """Delete a cart item by id and return True if removed."""
        logger.info("Deleting cart item id=%s", cart_item_id)
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE id = ?",
            (cart_item_id,),
        )
        logger.info("Cart item delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0

    def clear_cart_items(self, cart_id: int) -> int:
        """Delete all cart items for a cart and return count removed."""
        logger.info("Clearing cart items cart_id=%s", cart_id)
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE cart_id = ?",
            (cart_id,),
        )
        logger.info("Cleared %s cart items for cart_id=%s", cursor.rowcount, cart_id)
        return cursor.rowcount
