"""
Pydantic schemas for TimeEntry request/response validation.
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional
import logging

from pydantic import BaseModel, Field, field_validator

from backend.models.time_entry import TimeEntryStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class TimeEntryCreate(BaseModel):
    """Payload for creating time entries."""

    work_date: date = Field(..., description="Date when the work was performed")
    start_hour: time = Field(..., description="Start time of the work shift (e.g., '09:00')")
    end_hour: time = Field(..., description="End time of the work shift (e.g., '17:00')")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the work")

    @field_validator("end_hour")
    @classmethod
    def end_after_start(cls, v, info):
        """Ensure the end time is later than the start time."""
        logger.trace("Validating end hour after start")
        if "start_hour" in info.data and v <= info.data["start_hour"]:
            logger.warning("End hour before start hour")
            raise ValueError("End hour must be after start hour")
        return v


class TimeEntryUpdate(BaseModel):
    """Payload for updating time entries."""

    work_date: Optional[date] = Field(None, description="Date when the work was performed")
    start_hour: Optional[time] = Field(None, description="Start time of the work shift")
    end_hour: Optional[time] = Field(None, description="End time of the work shift")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the work")


class TimeEntryReview(BaseModel):
    """Payload for reviewing time entries."""

    status: TimeEntryStatus = Field(..., description="New status: 'accepted' or 'rejected'")
    rejection_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Required if status is 'rejected'. Reason for rejection."
    )

    @field_validator("rejection_reason")
    @classmethod
    def require_rejection_reason(cls, v, info):
        """Require a rejection reason when rejecting entries."""
        logger.trace("Validating rejection reason")
        if "status" in info.data and info.data["status"] == TimeEntryStatus.REJECTED:
            if not v or not v.strip():
                logger.warning("Missing rejection reason")
                raise ValueError("Rejection reason is required when rejecting a time entry")
        return v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TimeEntryResponse(BaseModel):
    """Response model for time entry data."""

    id: int
    employee_id: int
    work_date: date
    start_hour: time
    end_hour: time
    hours_worked: Decimal
    notes: Optional[str]
    status: TimeEntryStatus
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
