"""
Domain model representing a stock_entries row from the DB.

Each row records the current quantity on hand for a single item.
An item can only have ONE stock entry (item_id is UNIQUE in the table).
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class StockEntry:
    id: int
    item_id: int
    quantity: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Log the creation of the StockEntry model instance."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized StockEntry model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "StockEntry":
        """Build a StockEntry from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating StockEntry from database row")
        return cls(
            id=row["id"],
            item_id=row["item_id"],
            quantity=Decimal(str(row["quantity"])),
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
