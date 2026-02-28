"""
Repository layer for Cart persistence.
All SQL for the `carts` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.cart import Cart

logger = logging.getLogger(__name__)


class CartRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing CartRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, cart_id: int) -> Optional[Cart]:
        logger.trace("Fetching cart id=%s", cart_id)
        row = self._conn.execute(
            "SELECT * FROM carts WHERE id = ?",
            (cart_id,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    def get_by_desk_number(self, desk_number: str) -> Optional[Cart]:
        logger.trace("Fetching cart by desk_number=%s", desk_number)
        row = self._conn.execute(
            "SELECT * FROM carts WHERE desk_number = ?",
            (desk_number,),
        ).fetchone()
        return Cart.from_row(row) if row else None

    def list_with_desk_number(self) -> list[Cart]:
        logger.trace("Listing carts with desk_number")
        rows = self._conn.execute(
            "SELECT * FROM carts WHERE desk_number IS NOT NULL ORDER BY desk_number"
        ).fetchall()
        return [Cart.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, created_by: int) -> Cart:
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
