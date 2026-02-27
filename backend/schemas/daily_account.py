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
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal


class DailyAccountResponse(BaseModel):
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
    account: DailyAccountResponse
    items: list[DailyAccountItemResponse]
    totals: DailyAccountTotals


# ---------------------------------------------------------------------------
# Analysis Response schemas
# ---------------------------------------------------------------------------

class ItemSalesResponse(BaseModel):
    item_id: int
    total_quantity: float
    total_revenue: float
    days_sold: int
    avg_unit_price: float


class TopSellerResponse(BaseModel):
    item_id: int
    item_name: str
    sku: Optional[str]
    total_quantity: float
    total_revenue: float
    avg_unit_price: float


class CategorySalesResponse(BaseModel):
    category_id: int
    category_name: str
    total_quantity: float
    total_revenue: float
    items_count: int
