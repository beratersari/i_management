"""
Domain model (plain Python dataclass) representing a User row from the DB.
This is the internal representation used across service and repository layers.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    ADMIN = "admin"
    MARKET_OWNER = "market_owner"
    EMPLOYEE = "employee"


@dataclass
class User:
    id: int
    email: str
    username: str
    hashed_password: str
    role: UserRole
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    full_name: Optional[str] = None
    deleted_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized User model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "User":
        """Build a User from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating User from database row")
        deleted_at_raw = row["deleted_at"]
        return cls(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            full_name=row["full_name"],
            hashed_password=row["hashed_password"],
            role=UserRole(row["role"]),
            is_active=bool(row["is_active"]),
            is_deleted=bool(row["is_deleted"]),
            deleted_at=datetime.fromisoformat(deleted_at_raw) if deleted_at_raw else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
