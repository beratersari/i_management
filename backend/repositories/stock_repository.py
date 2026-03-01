"""
Repository layer for StockEntry persistence.
All SQL for the `stock_entries` table lives here.

Design rules enforced at DB level:
  - item_id is UNIQUE  →  one entry per item, no duplicates.
  - quantity >= 0       →  enforced by a CHECK constraint.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.stock import StockEntry
from backend.core.logging_config import log_db_timing

logger = logging.getLogger(__name__)


class StockRepository:
    """Data access layer for stock entry records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Store the database connection for query execution."""
        logger.trace("Initializing StockRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @log_db_timing
    def get_by_id(self, entry_id: int) -> Optional[StockEntry]:
        """Return a stock entry by its own primary key."""
        logger.trace("Fetching stock entry id=%s", entry_id)
        row = self._conn.execute(
            "SELECT * FROM stock_entries WHERE id = ?", (entry_id,)
        ).fetchone()
        return StockEntry.from_row(row) if row else None

    @log_db_timing
    def get_by_item_id(self, item_id: int) -> Optional[StockEntry]:
        """Return the stock entry for a specific item (None if not stocked yet)."""
        logger.trace("Fetching stock entry item_id=%s", item_id)
        row = self._conn.execute(
            "SELECT * FROM stock_entries WHERE item_id = ?", (item_id,)
        ).fetchone()
        return StockEntry.from_row(row) if row else None

    @log_db_timing
    def list_all(self) -> list[StockEntry]:
        """Return every stock entry ordered by item_id."""
        logger.trace("Listing stock entries")
        rows = self._conn.execute(
            "SELECT * FROM stock_entries ORDER BY item_id"
        ).fetchall()
        return [StockEntry.from_row(r) for r in rows]

    @log_db_timing
    def list_grouped_by_category(self) -> list[dict]:
        """
        Return all stocked items grouped by their category, sorted by item name
        within each group.

        Each dict in the returned list has:
            category_id   – int
            category_name – str
            items         – list[dict] with keys:
                              item_id, item_name, sku, unit_type,
                              unit_price, quantity, stock_entry_id
        """
        logger.trace("Listing stock grouped by category")
        rows = self._conn.execute(
            """
            SELECT
                c.id            AS category_id,
                c.name          AS category_name,
                i.id            AS item_id,
                i.name          AS item_name,
                i.sku           AS sku,
                i.unit_type     AS unit_type,
                i.unit_price    AS unit_price,
                se.id           AS stock_entry_id,
                se.quantity     AS quantity
            FROM stock_entries se
            JOIN items      i ON i.id  = se.item_id
            JOIN categories c ON c.id  = i.category_id
            ORDER BY c.name, i.name
            """
        ).fetchall()

        # Aggregate into {category_id → {meta, items[]}}
        groups: dict[int, dict] = {}
        for r in rows:
            cid = r["category_id"]
            if cid not in groups:
                groups[cid] = {
                    "category_id": cid,
                    "category_name": r["category_name"],
                    "items": [],
                }
            groups[cid]["items"].append(
                {
                    "stock_entry_id": r["stock_entry_id"],
                    "item_id": r["item_id"],
                    "item_name": r["item_name"],
                    "sku": r["sku"],
                    "unit_type": r["unit_type"],
                    "unit_price": r["unit_price"],
                    "quantity": r["quantity"],
                }
            )

        # Return as a list sorted by category name (already ordered by SQL)
        return list(groups.values())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @log_db_timing
    def add(
        self,
        item_id: int,
        quantity: float,
        created_by: int,
    ) -> StockEntry:
        """
        Insert a new stock entry for an item.
        Raises sqlite3.IntegrityError if item_id already exists (UNIQUE constraint).
        """
        logger.info("Creating stock entry item_id=%s", item_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO stock_entries (item_id, quantity, created_by, updated_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_id, quantity, created_by, created_by, now, now),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    @log_db_timing
    def update_quantity(
        self,
        item_id: int,
        quantity: float,
        updated_by: int,
    ) -> Optional[StockEntry]:
        """Update the quantity for an existing stock entry."""
        logger.info("Updating stock entry item_id=%s", item_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE stock_entries
               SET quantity = ?, updated_by = ?, updated_at = ?
             WHERE item_id = ?
            """,
            (quantity, updated_by, now, item_id),
        )
        return self.get_by_item_id(item_id)

    @log_db_timing
    def adjust_quantity(
        self,
        item_id: int,
        delta: float,
        updated_by: int,
    ) -> Optional[StockEntry]:
        """Adjust the quantity for an existing stock entry by a delta."""
        logger.info("Adjusting stock entry item_id=%s by delta=%s", item_id, delta)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE stock_entries
               SET quantity = quantity + ?, updated_by = ?, updated_at = ?
             WHERE item_id = ?
            """,
            (delta, updated_by, now, item_id),
        )
        return self.get_by_item_id(item_id)

    @log_db_timing
    def delete(self, item_id: int) -> bool:
        """Remove the stock entry for an item."""
        logger.info("Deleting stock entry item_id=%s", item_id)
        cursor = self._conn.execute(
            "DELETE FROM stock_entries WHERE item_id = ?", (item_id,)
        )
        logger.info("Stock delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0
