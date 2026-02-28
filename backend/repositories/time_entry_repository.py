"""
Repository layer for TimeEntry persistence.
All SQL for the `time_entries` table lives here.
"""
import sqlite3
from datetime import datetime, timezone, date, time
from decimal import Decimal
from typing import Optional
import logging

from backend.models.time_entry import TimeEntry, TimeEntryStatus

logger = logging.getLogger(__name__)


class TimeEntryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing TimeEntryRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, entry_id: int) -> Optional[TimeEntry]:
        logger.trace("Fetching time entry id=%s", entry_id)
        row = self._conn.execute(
            "SELECT * FROM time_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        return TimeEntry.from_row(row) if row else None

    def list_by_employee(
        self, 
        employee_id: int, 
        status: Optional[TimeEntryStatus] = None
    ) -> list[TimeEntry]:
        logger.trace("Listing time entries employee_id=%s status=%s", employee_id, status)
        if status:
            rows = self._conn.execute(
                """
                SELECT * FROM time_entries 
                WHERE employee_id = ? AND status = ?
                ORDER BY work_date DESC, created_at DESC
                """,
                (employee_id, status.value),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM time_entries 
                WHERE employee_id = ?
                ORDER BY work_date DESC, created_at DESC
                """,
                (employee_id,),
            ).fetchall()
        return [TimeEntry.from_row(row) for row in rows]

    def list_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        status: Optional[TimeEntryStatus] = None
    ) -> list[TimeEntry]:
        logger.trace("Listing time entries by date range")
        if status:
            rows = self._conn.execute(
                """
                SELECT * FROM time_entries 
                WHERE work_date >= ? AND work_date <= ? AND status = ?
                ORDER BY work_date DESC, employee_id
                """,
                (start_date.isoformat(), end_date.isoformat(), status.value),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM time_entries 
                WHERE work_date >= ? AND work_date <= ?
                ORDER BY work_date DESC, employee_id
                """,
                (start_date.isoformat(), end_date.isoformat()),
            ).fetchall()
        return [TimeEntry.from_row(row) for row in rows]

    def list_pending(self) -> list[TimeEntry]:
        """List all pending time entries (for admin/market_owner review)."""
        logger.trace("Listing pending time entries")
        rows = self._conn.execute(
            """
            SELECT * FROM time_entries 
            WHERE status = ?
            ORDER BY work_date DESC, created_at DESC
            """,
            (TimeEntryStatus.PENDING.value,),
        ).fetchall()
        return [TimeEntry.from_row(row) for row in rows]

    def list_all(self, limit: int = 100) -> list[TimeEntry]:
        logger.trace("Listing all time entries limit=%s", limit)
        rows = self._conn.execute(
            "SELECT * FROM time_entries ORDER BY work_date DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [TimeEntry.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        employee_id: int,
        work_date: date,
        start_hour: time,
        end_hour: time,
        hours_worked: Decimal,
        notes: Optional[str],
        created_by: int,
    ) -> TimeEntry:
        logger.info("Creating time entry employee_id=%s", employee_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            INSERT INTO time_entries (
                employee_id, work_date, start_hour, end_hour, hours_worked, notes,
                status, created_by, updated_by, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                work_date.isoformat(),
                start_hour.isoformat(),
                end_hour.isoformat(),
                float(hours_worked),
                notes,
                TimeEntryStatus.PENDING.value,
                created_by,
                created_by,
                now,
                now,
            ),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update(
        self,
        entry_id: int,
        work_date: Optional[date],
        start_hour: Optional[time],
        end_hour: Optional[time],
        hours_worked: Optional[Decimal],
        notes: Optional[str],
        updated_by: int,
    ) -> Optional[TimeEntry]:
        fields: dict = {}
        if work_date is not None:
            fields["work_date"] = work_date.isoformat()
        if start_hour is not None:
            fields["start_hour"] = start_hour.isoformat()
        if end_hour is not None:
            fields["end_hour"] = end_hour.isoformat()
        if hours_worked is not None:
            fields["hours_worked"] = float(hours_worked)
        if notes is not None:
            fields["notes"] = notes

        if not fields:
            logger.trace("No time entry fields to update id=%s", entry_id)
            return self.get_by_id(entry_id)

        logger.info("Updating time entry record id=%s", entry_id)
        fields["updated_by"] = updated_by
        fields["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [entry_id]
        self._conn.execute(
            f"UPDATE time_entries SET {set_clause} WHERE id = ?", values
        )
        return self.get_by_id(entry_id)

    def review(
        self,
        entry_id: int,
        status: TimeEntryStatus,
        reviewed_by: int,
        rejection_reason: Optional[str] = None,
    ) -> Optional[TimeEntry]:
        logger.info("Reviewing time entry record id=%s", entry_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE time_entries
               SET status = ?, reviewed_by = ?, reviewed_at = ?, 
                   rejection_reason = ?, updated_at = ?
             WHERE id = ?
            """,
            (status.value, reviewed_by, now, rejection_reason, now, entry_id),
        )
        return self.get_by_id(entry_id)

    def delete(self, entry_id: int) -> bool:
        logger.info("Deleting time entry record id=%s", entry_id)
        cursor = self._conn.execute(
            "DELETE FROM time_entries WHERE id = ?",
            (entry_id,),
        )
        logger.info("Time entry delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0
