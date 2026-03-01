"""
Domain model representing a time_entries row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from typing import Optional


class TimeEntryStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class TimeEntry:
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

    def __post_init__(self) -> None:
        """Log the creation of the TimeEntry model instance."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized TimeEntry model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "TimeEntry":
        """Build a TimeEntry from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating TimeEntry from database row")
        reviewed_at_raw = row["reviewed_at"]
        return cls(
            id=row["id"],
            employee_id=row["employee_id"],
            work_date=date.fromisoformat(row["work_date"]),
            start_hour=time.fromisoformat(row["start_hour"]),
            end_hour=time.fromisoformat(row["end_hour"]),
            hours_worked=Decimal(str(row["hours_worked"])),
            notes=row["notes"],
            status=TimeEntryStatus(row["status"]),
            reviewed_by=row["reviewed_by"],
            reviewed_at=datetime.fromisoformat(reviewed_at_raw) if reviewed_at_raw else None,
            rejection_reason=row["rejection_reason"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
