"""
Domain model representing a daily_account_items row from the DB.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class DailyAccountItem:
    id: int
    account_id: int
    item_id: int
    item_name: str
    sku: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    discount_rate: Decimal
    tax_rate: Decimal
    line_subtotal: Decimal
    line_discount: Decimal
    line_tax: Decimal
    line_total: Decimal
    created_at: datetime

    def __post_init__(self) -> None:
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized DailyAccountItem model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "DailyAccountItem":
        """Build a DailyAccountItem from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating DailyAccountItem from database row")
        return cls(
            id=row["id"],
            account_id=row["account_id"],
            item_id=row["item_id"],
            item_name=row["item_name"],
            sku=row["sku"],
            quantity=Decimal(str(row["quantity"])),
            unit_price=Decimal(str(row["unit_price"])),
            discount_rate=Decimal(str(row["discount_rate"])),
            tax_rate=Decimal(str(row["tax_rate"])),
            line_subtotal=Decimal(str(row["line_subtotal"])),
            line_discount=Decimal(str(row["line_discount"])),
            line_tax=Decimal(str(row["line_tax"])),
            line_total=Decimal(str(row["line_total"])),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
