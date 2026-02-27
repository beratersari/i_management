"""
Time entry management endpoints:
  POST   /time-entries                    – Create a new time entry (employees)
  GET    /time-entries                    – List my time entries
  GET    /time-entries/pending            – List pending entries (admin/market_owner)
  GET    /time-entries/by-date-range      – List entries by date range
  GET    /time-entries/{entry_id}         – Get a specific time entry
  PATCH  /time-entries/{entry_id}         – Update own time entry
  DELETE /time-entries/{entry_id}         – Delete own time entry
  POST   /time-entries/{entry_id}/review  – Review entry (admin/market_owner)
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException

from backend.core.dependencies import (
    db_dependency,
    get_current_active_user,
    require_admin_or_owner,
)
from backend.models.user import User
from backend.models.time_entry import TimeEntryStatus
from backend.schemas.time_entry import (
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryReview,
    TimeEntryResponse,
)
from backend.services.time_entry_service import TimeEntryService

router = APIRouter(prefix="/time-entries", tags=["Time Entries"])


@router.post(
    "",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new time entry",
)
def create_time_entry(
    data: TimeEntryCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new time entry for the current user.
    
    - **work_date**: Date when the work was performed (YYYY-MM-DD)
    - **start_hour**: Start time of the work shift (HH:MM, 24-hour format)
    - **end_hour**: End time of the work shift (HH:MM, 24-hour format)
    - **notes**: Optional notes about the work session
    """
    service = TimeEntryService(conn)
    return service.create_entry(data, current_user)


@router.get(
    "",
    response_model=list[TimeEntryResponse],
    summary="List my time entries",
)
def list_my_entries(
    status: Optional[TimeEntryStatus] = Query(
        None, 
        description="Filter by status: 'pending', 'accepted', or 'rejected'"
    ),
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Return all time entries for the current user."""
    service = TimeEntryService(conn)
    return service.list_my_entries(current_user, status)


@router.get(
    "/pending",
    response_model=list[TimeEntryResponse],
    summary="List all pending time entries (admin/market_owner only)",
)
def list_pending_entries(
    conn=Depends(db_dependency),
    _: User = Depends(require_admin_or_owner),
):
    """Return all pending time entries for review."""
    service = TimeEntryService(conn)
    return service.list_pending_entries()


@router.get(
    "/by-date-range",
    response_model=list[TimeEntryResponse],
    summary="List time entries by date range",
)
def list_entries_by_date_range(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    status: Optional[TimeEntryStatus] = Query(
        None, 
        description="Filter by status: 'pending', 'accepted', or 'rejected'"
    ),
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return time entries within a date range."""
    service = TimeEntryService(conn)
    return service.list_entries_by_date_range(start_date, end_date, status)


@router.get(
    "/{entry_id}",
    response_model=TimeEntryResponse,
    summary="Get a specific time entry",
)
def get_entry(
    entry_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return a specific time entry by ID."""
    service = TimeEntryService(conn)
    return service.get_entry(entry_id)


@router.patch(
    "/{entry_id}",
    response_model=TimeEntryResponse,
    summary="Update a time entry",
)
def update_entry(
    entry_id: int,
    data: TimeEntryUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a time entry.
    
    Employees can only update their own entries, and only if the status is 'pending'.
    """
    service = TimeEntryService(conn)
    return service.update_entry(entry_id, data, current_user)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a time entry",
)
def delete_entry(
    entry_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a time entry.
    
    Employees can only delete their own entries, and only if the status is 'pending'.
    """
    service = TimeEntryService(conn)
    service.delete_entry(entry_id, current_user)


@router.post(
    "/{entry_id}/review",
    response_model=TimeEntryResponse,
    summary="Review (accept/reject) a time entry (admin/market_owner only)",
)
def review_entry(
    entry_id: int,
    data: TimeEntryReview,
    conn=Depends(db_dependency),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Review a time entry (accept or reject).
    
    Only admin or market_owner can perform this action.
    
    - **status**: Set to 'accepted' or 'rejected'
    - **rejection_reason**: Required if status is 'rejected'
    """
    service = TimeEntryService(conn)
    return service.review_entry(entry_id, data, current_user)
