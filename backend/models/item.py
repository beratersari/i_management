"""
Domain model representing an Item row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Item:
    id: int
    category_id: int
    name: str
    description: Optional[str]
    sku: Optional[str]
    barcode: Optional[str]
    image_url: Optional[str]
    unit_price: Decimal
    unit_type: str
    tax_rate: Decimal
    discount_rate: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "Item":
        """Build an Item from a sqlite3.Row object."""
        return cls(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
            description=row["description"],
            sku=row["sku"],
            barcode=row["barcode"],
            image_url=row["image_url"],
            unit_price=Decimal(row["unit_price"]),
            unit_type=row["unit_type"],
            tax_rate=Decimal(row["tax_rate"]),
            discount_rate=Decimal(row["discount_rate"]),
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )