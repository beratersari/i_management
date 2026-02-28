"""
Domain model representing a cart row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Cart:
    id: int
    desk_number: str | None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized Cart model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "Cart":
        """Build a Cart from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating Cart from database row")
        return cls(
            id=row["id"],
            desk_number=row["desk_number"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
