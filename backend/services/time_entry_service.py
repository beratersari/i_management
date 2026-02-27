"""
Time entry management service.
Employees can create/edit/delete their own entries.
Admins and market owners can review (accept/reject) entries.
"""
import sqlite3
from datetime import date, time
from decimal import Decimal

from fastapi import HTTPException, status

from backend.models.time_entry import TimeEntry, TimeEntryStatus
from backend.models.user import User, UserRole
from backend.repositories.time_entry_repository import TimeEntryRepository
from backend.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate, TimeEntryReview


class TimeEntryService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo = TimeEntryRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_entry(self, entry_id: int) -> TimeEntry:
        entry = self._repo.get_by_id(entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Time entry with id={entry_id} not found",
            )
        return entry

    def list_my_entries(
        self, 
        user: User, 
        status_filter: TimeEntryStatus = None
    ) -> list[TimeEntry]:
        """List time entries for the current user."""
        return self._repo.list_by_employee(user.id, status=status_filter)

    def list_pending_entries(self) -> list[TimeEntry]:
        """List all pending entries (admin/market_owner only)."""
        return self._repo.list_pending()

    def list_entries_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        status_filter: TimeEntryStatus = None
    ) -> list[TimeEntry]:
        """List entries within a date range."""
        return self._repo.list_by_date_range(start_date, end_date, status=status_filter)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_entry(self, data: TimeEntryCreate, user: User) -> TimeEntry:
        """
        Create a new time entry for the current user.
        Automatically calculates hours worked from start and end times.
        """
        # Validate end time is after start time
        if data.end_hour <= data.start_hour:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End hour must be after start hour",
            )

        # Calculate hours worked
        hours_worked = self._calculate_hours(data.start_hour, data.end_hour)

        return self._repo.create(
            employee_id=user.id,
            work_date=data.work_date,
            start_hour=data.start_hour,
            end_hour=data.end_hour,
            hours_worked=hours_worked,
            notes=data.notes,
            created_by=user.id,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_entry(
        self, 
        entry_id: int, 
        data: TimeEntryUpdate, 
        user: User
    ) -> TimeEntry:
        """
        Update a time entry.
        Only the owner can update, and only if status is 'pending'.
        """
        entry = self.get_entry(entry_id)

        # Only owner can update
        if entry.employee_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own time entries",
            )

        # Can only update pending entries
        if entry.status != TimeEntryStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a time entry that has already been reviewed",
            )

        # Determine new values
        new_start = data.start_hour or entry.start_hour
        new_end = data.end_hour or entry.end_hour

        # Validate end time is after start time
        if new_end <= new_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End hour must be after start hour",
            )

        # Recalculate hours if times changed
        hours_worked = self._calculate_hours(new_start, new_end)

        return self._repo.update(
            entry_id=entry.id,
            work_date=data.work_date,
            start_hour=data.start_hour,
            end_hour=data.end_hour,
            hours_worked=hours_worked,
            notes=data.notes,
            updated_by=user.id,
        )  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_entry(self, entry_id: int, user: User) -> None:
        """
        Delete a time entry.
        Only the owner can delete, and only if status is 'pending'.
        """
        entry = self.get_entry(entry_id)

        # Only owner can delete
        if entry.employee_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own time entries",
            )

        # Can only delete pending entries
        if entry.status != TimeEntryStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a time entry that has already been reviewed",
            )

        if not self._repo.delete(entry.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Time entry with id={entry_id} not found",
            )

    # ------------------------------------------------------------------
    # Review (admin/market_owner only)
    # ------------------------------------------------------------------

    def review_entry(
        self, 
        entry_id: int, 
        data: TimeEntryReview, 
        reviewer: User
    ) -> TimeEntry:
        """
        Review a time entry (accept or reject).
        Only admin or market_owner can review.
        """
        entry = self.get_entry(entry_id)

        # Can only review pending entries
        if entry.status != TimeEntryStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Time entry is already {entry.status.value}",
            )

        # Validate rejection reason is provided when rejecting
        if data.status == TimeEntryStatus.REJECTED:
            if not data.rejection_reason or not data.rejection_reason.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason is required when rejecting a time entry",
                )

        return self._repo.review(
            entry_id=entry.id,
            status=data.status,
            reviewed_by=reviewer.id,
            rejection_reason=data.rejection_reason,
        )  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_hours(self, start: time, end: time) -> Decimal:
        """Calculate hours worked from start and end time."""
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        hours = Decimal(end_minutes - start_minutes) / Decimal(60)
        return hours.quantize(Decimal("0.01"))
