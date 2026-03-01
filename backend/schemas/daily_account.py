"""
Pydantic schemas for DailyAccount request/response validation.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DailyAccountItemResponse(BaseModel):
    """Response model for daily-account line items."""

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

    model_config = {"from_attributes": True}


class DailyAccountTotals(BaseModel):
    """Aggregate totals for a daily account."""

    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal


class DailyAccountResponse(BaseModel):
    """Response model for daily-account summary metadata."""

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

    model_config = {"from_attributes": True}


class DailyAccountSummaryResponse(BaseModel):
    """Bundled response for daily account details and totals."""

    account: DailyAccountResponse
    items: list[DailyAccountItemResponse]
    totals: DailyAccountTotals


# ---------------------------------------------------------------------------
# Analysis Response schemas
# ---------------------------------------------------------------------------

class ItemSalesResponse(BaseModel):
    """Response payload for item sales analytics."""

    item_id: int
    total_quantity: float
    total_revenue: float
    days_sold: int
    avg_unit_price: float


class TopSellerResponse(BaseModel):
    """Response payload for top-selling items."""

    item_id: int
    item_name: str
    sku: Optional[str]
    total_quantity: float
    total_revenue: float
    avg_unit_price: float


class CategorySalesResponse(BaseModel):
    """Response payload for category-level sales analytics."""

    category_id: int
    category_name: str
    total_quantity: float
    total_revenue: float
    items_count: int
