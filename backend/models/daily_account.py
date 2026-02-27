"""
Domain model representing a daily_accounts row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Optional


@dataclass
class DailyAccount:
    id: int
    account_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal
    carts_count: int
    items_count: int
    is_closed: bool
    closed_at: Optional[datetime]
    closed_by: Optional[int]
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> "DailyAccount":
        """Build a DailyAccount from a sqlite3.Row object."""
        closed_at_raw = row["closed_at"]
        return cls(
            id=row["id"],
            account_date=date.fromisoformat(row["account_date"]),
            subtotal=Decimal(str(row["subtotal"])),
            discount_total=Decimal(str(row["discount_total"])),
            tax_total=Decimal(str(row["tax_total"])),
            total=Decimal(str(row["total"])),
            carts_count=row["carts_count"],
            items_count=row["items_count"],
            is_closed=bool(row["is_closed"]),
            closed_at=datetime.fromisoformat(closed_at_raw) if closed_at_raw else None,
            closed_by=row["closed_by"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
