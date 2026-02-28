"""
Repository layer for DailyAccount persistence.
All SQL for the `daily_accounts` table lives here.
"""
import sqlite3
from datetime import datetime, timezone, date
from typing import Optional
import logging

from backend.models.daily_account import DailyAccount

logger = logging.getLogger(__name__)


class DailyAccountRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing DailyAccountRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, account_id: int) -> Optional[DailyAccount]:
        logger.trace("Fetching daily account id=%s", account_id)
        row = self._conn.execute(
            "SELECT * FROM daily_accounts WHERE id = ?",
            (account_id,),
        ).fetchone()
        return DailyAccount.from_row(row) if row else None

    def get_by_date(self, account_date: date) -> Optional[DailyAccount]:
        logger.trace("Fetching daily account by date=%s", account_date)
        row = self._conn.execute(
            "SELECT * FROM daily_accounts WHERE account_date = ?",
            (account_date.isoformat(),),
        ).fetchone()
        return DailyAccount.from_row(row) if row else None

    def list_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[DailyAccount]:
        logger.trace("Listing daily accounts range %s-%s", start_date, end_date)
        rows = self._conn.execute(
            """
            SELECT * FROM daily_accounts
             WHERE account_date >= ? AND account_date <= ?
             ORDER BY account_date DESC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()
        return [DailyAccount.from_row(row) for row in rows]

    def list_all(self, limit: int = 30) -> list[DailyAccount]:
        logger.trace("Listing daily accounts limit=%s", limit)
        rows = self._conn.execute(
            "SELECT * FROM daily_accounts ORDER BY account_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [DailyAccount.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        account_date: date,
        subtotal: float,
        discount_total: float,
        tax_total: float,
        total: float,
        carts_count: int,
        items_count: int,
        created_by: int,
    ) -> DailyAccount:
        logger.info("Creating daily account date=%s", account_date)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO daily_accounts (
                account_date, subtotal, discount_total, tax_total, total,
                carts_count, items_count, created_by, updated_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_date.isoformat(),
                subtotal,
                discount_total,
                tax_total,
                total,
                carts_count,
                items_count,
                created_by,
                created_by,
                now,
                now,
            ),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def close_account(
        self,
        account_id: int,
        closed_by: int,
    ) -> Optional[DailyAccount]:
        logger.info("Closing daily account id=%s", account_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE daily_accounts
               SET is_closed = 1, closed_at = ?, closed_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (now, closed_by, now, account_id),
        )
        return self.get_by_id(account_id)

    def open_account(
        self,
        account_id: int,
        opened_by: int,
    ) -> Optional[DailyAccount]:
        """Reopen a closed account (admin/market_owner only)."""
        logger.info("Opening daily account id=%s", account_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE daily_accounts
               SET is_closed = 0, closed_at = NULL, closed_by = NULL, updated_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (opened_by, now, account_id),
        )
        return self.get_by_id(account_id)

    def update_totals(
        self,
        account_id: int,
        subtotal: float,
        discount_total: float,
        tax_total: float,
        total: float,
        carts_count: int,
        items_count: int,
        updated_by: int,
    ) -> Optional[DailyAccount]:
        logger.info("Updating daily account totals id=%s", account_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE daily_accounts
               SET subtotal = ?, discount_total = ?, tax_total = ?, total = ?,
                   carts_count = ?, items_count = ?, updated_by = ?, updated_at = ?
             WHERE id = ?
            """,
            (subtotal, discount_total, tax_total, total, carts_count, items_count, updated_by, now, account_id),
        )
        return self.get_by_id(account_id)
