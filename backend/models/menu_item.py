"""
Domain model representing a menu_items row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MenuItem:
    id: int
    item_id: int
    display_name: str
    description: str | None
    allergens: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Log the creation of the MenuItem model instance."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized MenuItem model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "MenuItem":
        """Build a MenuItem from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating MenuItem from database row")
        return cls(
            id=row["id"],
            item_id=row["item_id"],
            display_name=row["display_name"],
            description=row["description"],
            allergens=row["allergens"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
