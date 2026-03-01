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
    sort_order: int
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Log the creation of the Category model instance."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized Category model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "Category":
        """Build a Category from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating Category from database row")
        return cls(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            sort_order=row["sort_order"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )