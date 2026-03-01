"""
Repository layer for Cart persistence.
All SQL for the `carts` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import logging

from backend.models.cart import Cart, CartStatus
from backend.models.cart_item import CartItem
from backend.core.logging_config import log_db_timing

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

    @log_db_timing
    def get_by_id(self, cart_id: int) -> Optional[Cart]:
        """Return a cart by its id or None if missing."""
        logger.trace("Fetching cart id=%s", cart_id)
        row = self._conn.execute(
            "SELECT * FROM carts WHERE id = ?",
            (cart_id,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    @log_db_timing
    def get_by_desk_number(self, desk_number: str) -> Optional[Cart]:
        """Return a cart by its desk number, if assigned."""
        logger.trace("Fetching cart by desk_number=%s", desk_number)
        row = self._conn.execute(
            "SELECT * FROM carts WHERE desk_number = ?",
            (desk_number,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    @log_db_timing
    def list_with_desk_number(self) -> list[Cart]:
        """List all carts that have a desk number assigned."""
        logger.trace("Listing carts with desk_number")
        rows = self._conn.execute(
            "SELECT * FROM carts WHERE desk_number IS NOT NULL ORDER BY desk_number"
        ).fetchall()
        return [Cart.from_row(r) for r in rows]

    @log_db_timing
    def list_by_date_range(
        self, start_date: str, end_date: str, status: Optional[CartStatus] = None
    ) -> list[Cart]:
        """List carts within a date range, optionally filtered by status."""
        logger.trace("Listing carts by date range %s to %s, status=%s", start_date, end_date, status)
        
        if status:
            rows = self._conn.execute(
                """
                SELECT * FROM carts 
                WHERE created_at >= ? AND created_at < ?
                AND status = ?
                ORDER BY created_at
                """,
                (start_date, end_date, status.value),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM carts 
                WHERE created_at >= ? AND created_at < ?
                ORDER BY created_at
                """,
                (start_date, end_date),
            ).fetchall()
        return [Cart.from_row(r) for r in rows]

    @log_db_timing
    def list_completed_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """List completed carts with their totals and item details for sales reporting."""
        logger.trace("Listing completed carts by date range %s to %s", start_date, end_date)
        rows = self._conn.execute(
            """
            SELECT 
                c.id,
                c.desk_number,
                c.status,
                c.created_at,
                c.updated_at,
                COUNT(ci.id) as item_count,
                COALESCE(SUM(ci.quantity * i.unit_price), 0) as subtotal,
                COALESCE(SUM(ci.quantity * i.unit_price * i.discount_rate / 100), 0) as discount_total,
                COALESCE(SUM(ci.quantity * i.unit_price * (1 - i.discount_rate / 100) * i.tax_rate / 100), 0) as tax_total,
                COALESCE(SUM(ci.quantity * i.unit_price * (1 - i.discount_rate / 100) * (1 + i.tax_rate / 100)), 0) as total
            FROM carts c
            LEFT JOIN cart_items ci ON ci.cart_id = c.id
            LEFT JOIN items i ON i.id = ci.item_id
            WHERE c.created_at >= ? AND c.created_at < ?
            AND c.status = 'completed'
            GROUP BY c.id
            ORDER BY c.created_at
            """,
            (start_date, end_date),
        ).fetchall()
        
        cart_rows = [
            {
                "id": r["id"],
                "desk_number": r["desk_number"],
                "status": r["status"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "item_count": r["item_count"],
                "subtotal": Decimal(str(r["subtotal"])),
                "discount_total": Decimal(str(r["discount_total"])),
                "tax_total": Decimal(str(r["tax_total"])),
                "total": Decimal(str(r["total"])),
            }
            for r in rows
        ]
        
        if not cart_rows:
            return []
        
        cart_ids = tuple(row["id"] for row in cart_rows)
        placeholders = ", ".join("?" for _ in cart_ids)
        item_rows = self._conn.execute(
            f"""
            SELECT 
                ci.cart_id,
                ci.id AS cart_item_id,
                ci.quantity,
                i.id AS item_id,
                i.name,
                i.sku,
                i.unit_price,
                i.discount_rate,
                i.tax_rate
            FROM cart_items ci
            JOIN items i ON i.id = ci.item_id
            WHERE ci.cart_id IN ({placeholders})
            ORDER BY ci.cart_id, ci.id
            """,
            cart_ids,
        ).fetchall()
        
        items_by_cart: dict[int, list[dict]] = {}
        for row in item_rows:
            items_by_cart.setdefault(row["cart_id"], []).append(
                {
                    "cart_item_id": row["cart_item_id"],
                    "item_id": row["item_id"],
                    "name": row["name"],
                    "sku": row["sku"],
                    "quantity": Decimal(str(row["quantity"])),
                    "unit_price": Decimal(str(row["unit_price"])),
                    "discount_rate": Decimal(str(row["discount_rate"])),
                    "tax_rate": Decimal(str(row["tax_rate"])),
                }
            )
        
        for cart in cart_rows:
            cart["items"] = items_by_cart.get(cart["id"], [])
        
        return cart_rows

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @log_db_timing
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

    @log_db_timing
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

    @log_db_timing
    def update_status(self, cart_id: int, status: CartStatus, updated_by: int) -> Optional[Cart]:
        """Update a cart's status and return the updated row."""
        logger.info("Updating cart id=%s status=%s", cart_id, status.value)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE carts
               SET status = ?, updated_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (status.value, updated_by, now, cart_id),
        )
        return self.get_by_id(cart_id)

    @log_db_timing
    def touch(self, cart_id: int, updated_by: int) -> None:
        """Update the updated_at timestamp for a cart."""
        logger.trace("Touching cart id=%s", cart_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE carts SET updated_by = ?, updated_at = ? WHERE id = ?",
            (updated_by, now, cart_id),
        )

    # ------------------------------------------------------------------
    # Cart items
    # ------------------------------------------------------------------

    @log_db_timing
    def get_cart_item_by_id(self, cart_item_id: int) -> Optional[CartItem]:
        """Return a cart item by its id or None if missing."""
        logger.trace("Fetching cart item id=%s", cart_item_id)
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE id = ?",
            (cart_item_id,),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    @log_db_timing
    def get_cart_item_by_cart_and_item(self, cart_id: int, item_id: int) -> Optional[CartItem]:
        """Return a cart item for the given cart and item ids."""
        logger.trace("Fetching cart item cart_id=%s item_id=%s", cart_id, item_id)
        row = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?",
            (cart_id, item_id),
        ).fetchone()
        return CartItem.from_row(row) if row else None

    @log_db_timing
    def list_cart_items_by_cart(self, cart_id: int) -> list[CartItem]:
        """Return all cart items for a given cart."""
        logger.trace("Listing cart items cart_id=%s", cart_id)
        rows = self._conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? ORDER BY id",
            (cart_id,),
        ).fetchall()
        return [CartItem.from_row(row) for row in rows]

    @log_db_timing
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

    @log_db_timing
    def update_cart_item_quantity(
        self,
        cart_item_id: int,
        quantity: Decimal,
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
            (float(quantity), updated_by, now, cart_item_id),
        )
        return self.get_cart_item_by_id(cart_item_id)

    @log_db_timing
    def delete_cart_item(self, cart_item_id: int) -> bool:
        """Delete a cart item by id and return True if removed."""
        logger.info("Deleting cart item id=%s", cart_item_id)
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE id = ?",
            (cart_item_id,),
        )
        logger.info("Cart item delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0

    @log_db_timing
    def clear_cart_items(self, cart_id: int) -> int:
        """Delete all cart items for a cart and return count removed."""
        logger.info("Clearing cart items cart_id=%s", cart_id)
        cursor = self._conn.execute(
            "DELETE FROM cart_items WHERE cart_id = ?",
            (cart_id,),
        )
        logger.info("Cleared %s cart items for cart_id=%s", cursor.rowcount, cart_id)
        return cursor.rowcount
