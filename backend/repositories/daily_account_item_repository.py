"""
Repository layer for DailyAccountItem persistence.
All SQL for the `daily_account_items` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.daily_account_item import DailyAccountItem

logger = logging.getLogger(__name__)


class DailyAccountItemRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing DailyAccountItemRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, item_id: int) -> Optional[DailyAccountItem]:
        logger.trace("Fetching daily account item id=%s", item_id)
        row = self._conn.execute(
            "SELECT * FROM daily_account_items WHERE id = ?",
            (item_id,),
        ).fetchone()
        return DailyAccountItem.from_row(row) if row else None

    def list_by_account(self, account_id: int) -> list[DailyAccountItem]:
        logger.trace("Listing daily account items account_id=%s", account_id)
        rows = self._conn.execute(
            "SELECT * FROM daily_account_items WHERE account_id = ? ORDER BY id",
            (account_id,),
        ).fetchall()
        return [DailyAccountItem.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        account_id: int,
        item_id: int,
        item_name: str,
        sku: Optional[str],
        quantity: float,
        unit_price: float,
        discount_rate: float,
        tax_rate: float,
        line_subtotal: float,
        line_discount: float,
        line_tax: float,
        line_total: float,
    ) -> DailyAccountItem:
        logger.info("Creating daily account item account_id=%s item_id=%s", account_id, item_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO daily_account_items (
                account_id, item_id, item_name, sku, quantity,
                unit_price, discount_rate, tax_rate,
                line_subtotal, line_discount, line_tax, line_total, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                item_id,
                item_name,
                sku,
                quantity,
                unit_price,
                discount_rate,
                tax_rate,
                line_subtotal,
                line_discount,
                line_tax,
                line_total,
                now,
            ),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def delete_by_account(self, account_id: int) -> int:
        logger.info("Deleting daily account items account_id=%s", account_id)
        cursor = self._conn.execute(
            "DELETE FROM daily_account_items WHERE account_id = ?",
            (account_id,),
        )
        logger.info("Daily account items delete affected %s rows", cursor.rowcount)
        return cursor.rowcount

    def get_item_sales_by_date_range(
        self, item_id: int, start_date: str, end_date: str
    ) -> dict:
        """Get sales statistics for a specific item within a date range."""
        logger.trace("Getting item sales item_id=%s", item_id)
        row = self._conn.execute(
            """
            SELECT 
                SUM(dai.quantity) as total_quantity,
                SUM(dai.line_total) as total_revenue,
                COUNT(DISTINCT da.id) as days_sold,
                AVG(dai.unit_price) as avg_unit_price
            FROM daily_account_items dai
            JOIN daily_accounts da ON da.id = dai.account_id
            WHERE dai.item_id = ?
              AND da.account_date >= ?
              AND da.account_date <= ?
              AND da.is_closed = 1
            """,
            (item_id, start_date, end_date),
        ).fetchone()

        if not row or row["total_quantity"] is None:
            logger.trace("No sales data for item_id=%s", item_id)
            return {
                "item_id": item_id,
                "total_quantity": 0,
                "total_revenue": 0.0,
                "days_sold": 0,
                "avg_unit_price": 0.0,
            }

        return {
            "item_id": item_id,
            "total_quantity": row["total_quantity"],
            "total_revenue": row["total_revenue"],
            "days_sold": row["days_sold"],
            "avg_unit_price": row["avg_unit_price"],
        }

    def get_top_sellers(
        self, start_date: str, end_date: str, limit: int = 10
    ) -> list[dict]:
        """Get top selling items within a date range."""
        logger.trace("Getting top sellers start_date=%s end_date=%s", start_date, end_date)
        rows = self._conn.execute(
            """
            SELECT 
                dai.item_id,
                dai.item_name,
                dai.sku,
                SUM(dai.quantity) as total_quantity,
                SUM(dai.line_total) as total_revenue,
                AVG(dai.unit_price) as avg_unit_price
            FROM daily_account_items dai
            JOIN daily_accounts da ON da.id = dai.account_id
            WHERE da.account_date >= ?
              AND da.account_date <= ?
              AND da.is_closed = 1
            GROUP BY dai.item_id, dai.item_name, dai.sku
            ORDER BY total_quantity DESC
            LIMIT ?
            """,
            (start_date, end_date, limit),
        ).fetchall()

        return [
            {
                "item_id": row["item_id"],
                "item_name": row["item_name"],
                "sku": row["sku"],
                "total_quantity": row["total_quantity"],
                "total_revenue": row["total_revenue"],
                "avg_unit_price": row["avg_unit_price"],
            }
            for row in rows
        ]

    def get_sales_by_category(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """Get sales aggregated by category within a date range."""
        logger.trace("Getting sales by category start_date=%s end_date=%s", start_date, end_date)
        rows = self._conn.execute(
            """
            SELECT 
                c.id as category_id,
                c.name as category_name,
                SUM(dai.quantity) as total_quantity,
                SUM(dai.line_total) as total_revenue,
                COUNT(DISTINCT dai.item_id) as items_count
            FROM daily_account_items dai
            JOIN daily_accounts da ON da.id = dai.account_id
            JOIN items i ON i.id = dai.item_id
            JOIN categories c ON c.id = i.category_id
            WHERE da.account_date >= ?
              AND da.account_date <= ?
              AND da.is_closed = 1
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
            """,
            (start_date, end_date),
        ).fetchall()

        return [
            {
                "category_id": row["category_id"],
                "category_name": row["category_name"],
                "total_quantity": row["total_quantity"],
                "total_revenue": row["total_revenue"],
                "items_count": row["items_count"],
            }
            for row in rows
        ]
