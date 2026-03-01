"""
Time entry management service.
Employees can create/edit/delete their own entries.
Admins and market owners can review (accept/reject) entries.
"""
import sqlite3
from datetime import date, time
from decimal import Decimal
from io import BytesIO
import logging
from typing import Optional

from fastapi import HTTPException, status

from backend.models.time_entry import TimeEntry, TimeEntryStatus
from backend.models.user import User, UserRole
from backend.repositories.time_entry_repository import TimeEntryRepository
from backend.repositories.user_repository import UserRepository
from backend.schemas.time_entry import TimeEntryCreate, TimeEntryUpdate, TimeEntryReview, EmployeeTimeEntries, GroupedTimeEntriesResponse
from backend.services.pdf_service import PDFService

logger = logging.getLogger(__name__)


class TimeEntryService:
    """Business logic for time entry management and reviews."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize the repository used by the time entry service."""
        logger.trace("Initializing TimeEntryService")
        self._conn = conn
        self._repo = TimeEntryRepository(conn)
        self._user_repo = UserRepository(conn)
        self._pdf_service = PDFService()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_entry(self, entry_id: int) -> TimeEntry:
        """Fetch a time entry by id or raise a 404 HTTP exception."""
        logger.info("Fetching time entry id=%s", entry_id)
        entry = self._repo.get_by_id(entry_id)
        if not entry:
            logger.warning("Time entry id=%s not found", entry_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Time entry with id={entry_id} not found",
            )
        return entry

    def list_my_entries(
        self,
        user: User,
        status_filter: TimeEntryStatus = None,
    ) -> list[TimeEntry]:
        """List time entries for the current user."""
        logger.info("Listing time entries for user id=%s", user.id)
        return self._repo.list_by_employee(user.id, status=status_filter)

    def list_pending_entries(self) -> list[TimeEntry]:
        """List all pending entries (admin/market_owner only)."""
        logger.info("Listing pending time entries")
        return self._repo.list_pending()

    def list_entries_by_date_range(
        self,
        start_date: date,
        end_date: date,
        status_filter: TimeEntryStatus = None,
    ) -> list[TimeEntry]:
        """List entries within a date range."""
        logger.info("Listing time entries from %s to %s", start_date, end_date)
        return self._repo.list_by_date_range(start_date, end_date, status=status_filter)

    def list_grouped_by_employee(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status_filter: Optional[TimeEntryStatus] = None,
    ) -> GroupedTimeEntriesResponse:
        """
        List all time entries grouped by employee.
        
        Args:
            start_date: Optional start date for the query
            end_date: Optional end date for the query
            status_filter: Optional status filter (pending, accepted, rejected)
            
        Returns:
            GroupedTimeEntriesResponse with entries grouped by employee
        """
        logger.info(
            "Listing time entries grouped by employee from %s to %s, status=%s",
            start_date, end_date, status_filter
        )
        
        # Get all entries
        entries = self._repo.list_by_date_range(start_date, end_date, status=status_filter)
        
        # Group by employee
        employee_groups: dict[int, list[TimeEntry]] = {}
        for entry in entries:
            if entry.employee_id not in employee_groups:
                employee_groups[entry.employee_id] = []
            employee_groups[entry.employee_id].append(entry)
        
        # Build response with employee names
        employee_time_entries: list[EmployeeTimeEntries] = []
        total_hours = Decimal('0')
        total_entries = 0
        
        for employee_id, emp_entries in employee_groups.items():
            employee = self._user_repo.get_by_id(employee_id)
            employee_name = employee.full_name or employee.username if employee else f"Employee {employee_id}"
            
            emp_total_hours = sum(e.hours_worked for e in emp_entries)
            total_hours += emp_total_hours
            total_entries += len(emp_entries)
            
            employee_time_entries.append(EmployeeTimeEntries(
                employee_id=employee_id,
                employee_name=employee_name,
                entries=emp_entries,
                total_hours=emp_total_hours,
                entry_count=len(emp_entries),
            ))
        
        # Sort by employee name
        employee_time_entries.sort(key=lambda x: x.employee_name)
        
        return GroupedTimeEntriesResponse(
            employees=employee_time_entries,
            total_hours=total_hours,
            total_entries=total_entries,
        )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_entry(self, data: TimeEntryCreate, user: User) -> TimeEntry:
        """
        Create a new time entry for the current user.
        Automatically calculates hours worked from start and end times.
        Supports overnight shifts with end_date.
        """
        logger.info("Creating time entry for user id=%s", user.id)
        
        # Calculate hours worked
        hours_worked = self._calculate_hours(data.start_hour, data.end_hour)

        entry = self._repo.create(
            employee_id=user.id,
            work_date=data.work_date,
            end_date=data.end_date,
            start_hour=data.start_hour,
            end_hour=data.end_hour,
            hours_worked=hours_worked,
            notes=data.notes,
            created_by=user.id,
        )
        logger.info("Time entry created id=%s", entry.id)
        return entry

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_entry(
        self,
        entry_id: int,
        data: TimeEntryUpdate,
        user: User,
    ) -> TimeEntry:
        """
        Update a time entry.
        Employees can only update their own pending entries.
        Admins and market_owners can update any entry.
        """
        logger.info("Updating time entry id=%s", entry_id)
        entry = self.get_entry(entry_id)

        # Check if user is admin or market_owner
        is_admin_or_owner = user.role in (UserRole.ADMIN, UserRole.MARKET_OWNER)

        # Only owner can update their own entries, unless admin/market_owner
        if entry.employee_id != user.id and not is_admin_or_owner:
            logger.warning("User id=%s cannot update entry id=%s", user.id, entry_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own time entries",
            )

        # Employees can only update pending entries
        # Admins and market_owners can update any entry
        if entry.status != TimeEntryStatus.PENDING and not is_admin_or_owner:
            logger.warning("Time entry id=%s already reviewed", entry_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a time entry that has already been reviewed",
            )

        # Determine new values
        new_start = data.start_hour or entry.start_hour
        new_end = data.end_hour or entry.end_hour
        new_end_date = data.end_date if data.end_date is not None else entry.end_date

        # Recalculate hours
        hours_worked = self._calculate_hours(new_start, new_end)

        updated_entry = self._repo.update(
            entry_id=entry.id,
            work_date=data.work_date,
            end_date=new_end_date,
            start_hour=data.start_hour,
            end_hour=data.end_hour,
            hours_worked=hours_worked,
            notes=data.notes,
            updated_by=user.id,
        )  # type: ignore[return-value]
        logger.info("Time entry updated id=%s", entry.id)
        return updated_entry

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_entry(self, entry_id: int, user: User) -> None:
        """
        Delete a time entry.
        Only the owner can delete, and only if status is 'pending'.
        """
        logger.info("Deleting time entry id=%s", entry_id)
        entry = self.get_entry(entry_id)

        # Only owner can delete
        if entry.employee_id != user.id:
            logger.warning("User id=%s cannot delete entry id=%s", user.id, entry_id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own time entries",
            )

        # Can only delete pending entries
        if entry.status != TimeEntryStatus.PENDING:
            logger.warning("Time entry id=%s already reviewed", entry_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a time entry that has already been reviewed",
            )

        if not self._repo.delete(entry.id):
            logger.warning("Time entry id=%s not found for deletion", entry_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Time entry with id={entry_id} not found",
            )
        logger.info("Time entry deleted id=%s", entry.id)

    # ------------------------------------------------------------------
    # Review (admin/market_owner only)
    # ------------------------------------------------------------------

    def review_entry(
        self,
        entry_id: int,
        data: TimeEntryReview,
        reviewer: User,
    ) -> TimeEntry:
        """Review a time entry as an admin or market owner."""
        logger.info("Reviewing time entry id=%s", entry_id)
        entry = self.get_entry(entry_id)

        # Can only review pending entries
        if entry.status != TimeEntryStatus.PENDING:
            logger.warning("Time entry id=%s already reviewed", entry_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Time entry is already {entry.status.value}",
            )

        # Validate rejection reason is provided when rejecting
        if data.status == TimeEntryStatus.REJECTED:
            if not data.rejection_reason or not data.rejection_reason.strip():
                logger.warning("Missing rejection reason for entry id=%s", entry_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rejection reason is required when rejecting a time entry",
                )

        reviewed_entry = self._repo.review(
            entry_id=entry.id,
            status=data.status,
            reviewed_by=reviewer.id,
            rejection_reason=data.rejection_reason,
        )  # type: ignore[return-value]
        logger.info("Time entry reviewed id=%s status=%s", entry.id, data.status.value)
        return reviewed_entry

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_hours(self, start: time, end: time) -> Decimal:
        """
        Calculate hours worked from start and end time.
        """
        logger.trace("Calculating hours worked")
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        
        hours = Decimal(end_minutes - start_minutes) / Decimal(60)
        return hours.quantize(Decimal("0.01"))

    def _detect_overlaps(self, entries: list[dict]) -> set[int]:
        """
        Detect overlapping time entries for the same employee.
        Returns a set of entry IDs that have overlaps.
        """
        overlapping_ids = set()
        
        # Group by employee
        by_employee: dict[int, list[dict]] = {}
        for entry in entries:
            emp_id = entry['employee_id']
            if emp_id not in by_employee:
                by_employee[emp_id] = []
            by_employee[emp_id].append(entry)
        
        # Check overlaps within each employee's entries
        for emp_id, emp_entries in by_employee.items():
            # Sort by work_date and start_hour
            sorted_entries = sorted(emp_entries, key=lambda x: (x['work_date'], str(x['start_hour'])))
            
            for i, entry1 in enumerate(sorted_entries):
                for entry2 in sorted_entries[i+1:]:
                    # Check if entries overlap
                    if self._entries_overlap(entry1, entry2):
                        overlapping_ids.add(entry1['id'])
                        overlapping_ids.add(entry2['id'])
        
        return overlapping_ids

    def _entries_overlap(self, entry1: dict, entry2: dict) -> bool:
        """Check if two time entries overlap."""
        from datetime import datetime, timedelta
        
        # Get start and end datetimes for entry1
        start1 = datetime.combine(entry1['work_date'], entry1['start_hour'])
        end_date1 = entry1.get('end_date') or entry1['work_date']
        end1 = datetime.combine(end_date1, entry1['end_hour'])
        if end1 <= start1:
            end1 += timedelta(days=1)  # Overnight shift
        
        # Get start and end datetimes for entry2
        start2 = datetime.combine(entry2['work_date'], entry2['start_hour'])
        end_date2 = entry2.get('end_date') or entry2['work_date']
        end2 = datetime.combine(end_date2, entry2['end_hour'])
        if end2 <= start2:
            end2 += timedelta(days=1)  # Overnight shift
        
        # Check overlap
        return start1 < end2 and start2 < end1

    # ------------------------------------------------------------------
    # PDF Export
    # ------------------------------------------------------------------

    def export_working_time_pdf(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        employee_id: Optional[int] = None,
        status_filter: Optional[TimeEntryStatus] = None,
    ) -> BytesIO:
        """
        Export working time entries as a PDF document.
        
        Args:
            start_date: Optional start date for the report
            end_date: Optional end date for the report
            employee_id: Optional employee ID to filter by specific employee
            status_filter: Optional status filter (defaults to accepted if not provided)
            
        Returns:
            BytesIO buffer containing the PDF
        """
        logger.info(
            "Exporting working time PDF from %s to %s, employee_id=%s, status=%s",
            start_date, end_date, employee_id, status_filter
        )
        
        # Get time entries - default to accepted if no status filter provided
        effective_status = status_filter or TimeEntryStatus.ACCEPTED
        
        if employee_id:
            # We need to update this repo method too or use list_by_date_range and filter
            entries = self._repo.list_by_date_range(
                start_date=start_date,
                end_date=end_date,
                status=effective_status,
            )
            entries = [e for e in entries if e.employee_id == employee_id]
            
            employee = self._user_repo.get_by_id(employee_id)
            employee_name = employee.full_name or employee.username if employee else f"Employee {employee_id}"
        else:
            entries = self._repo.list_by_date_range(
                start_date=start_date,
                end_date=end_date,
                status=effective_status,
            )
            employee_name = None
        
        # Enrich entries with employee names
        enriched_entries = []
        for entry in entries:
            employee = self._user_repo.get_by_id(entry.employee_id)
            entry_dict = {
                'id': entry.id,
                'employee_id': entry.employee_id,
                'employee_name': employee.full_name or employee.username if employee else f"Employee {entry.employee_id}",
                'work_date': entry.work_date,
                'start_hour': entry.start_hour,
                'end_hour': entry.end_hour,
                'hours_worked': entry.hours_worked,
                'status': entry.status,
                'notes': entry.notes,
            }
            enriched_entries.append(entry_dict)
        
        # Generate PDF
        pdf_buffer = self._pdf_service.generate_working_time_report(
            time_entries=enriched_entries,
            start_date=start_date,
            end_date=end_date,
            employee_name=employee_name,
        )
        
        logger.info("Working time PDF generated with %d entries", len(enriched_entries))
        return pdf_buffer
