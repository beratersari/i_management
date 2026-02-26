"""
Pydantic schemas for StockEntry request/response validation.
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class StockCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="ID of the item to add to stock")
    quantity: Decimal = Field(..., ge=0, decimal_places=3, description="Initial quantity on hand")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        return Decimal(str(v)) if v is not None else v


class StockUpdate(BaseModel):
    quantity: Decimal = Field(..., ge=0, decimal_places=3, description="New quantity on hand")

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        return Decimal(str(v)) if v is not None else v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class StockEntryResponse(BaseModel):
    id: int
    item_id: int
    quantity: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockItemSummary(BaseModel):
    """Flat item row used inside a grouped-by-category response."""
    stock_entry_id: int
    item_id: int
    item_name: str
    sku: Optional[str]
    unit_type: str
    unit_price: float
    quantity: float


class StockCategoryGroup(BaseModel):
    """One category bucket returned by the grouped stock endpoint."""
    category_id: int
    category_name: str
    items: list[StockItemSummary]
