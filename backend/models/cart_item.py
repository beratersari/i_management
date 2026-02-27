"""
Domain model representing a cart_items row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class CartItem:
    id: int
    cart_id: int
    item_id: int
    quantity: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "CartItem":
        """Build a CartItem from a sqlite3.Row object."""
        return cls(
            id=row["id"],
            cart_id=row["cart_id"],
            item_id=row["item_id"],
            quantity=Decimal(str(row["quantity"])),
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
