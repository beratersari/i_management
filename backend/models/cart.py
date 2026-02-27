"""
Domain model representing a cart row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Cart:
    id: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "Cart":
        """Build a Cart from a sqlite3.Row object."""
        return cls(
            id=row["id"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
