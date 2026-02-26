"""
Domain model representing a Category row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    description: Optional[str]
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "Category":
        """Build a Category from a sqlite3.Row object."""
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )