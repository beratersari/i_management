"""
Pydantic schemas for Cart request/response validation.
"""
from datetime import datetime
from decimal import Decimal
import logging

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CartCreate(BaseModel):
    """Empty payload for creating a cart (user context provides creator)."""


class CartUpdate(BaseModel):
    desk_number: str | None = Field(None, min_length=1, max_length=20, description="Optional desk/table identifier for cafe orders")


class CartItemCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="ID of the item to add")
    quantity: Decimal = Field(..., gt=0, decimal_places=3)

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        logger.trace("Coercing cart decimal value")
        return Decimal(str(v)) if v is not None else v


class CartItemUpdate(BaseModel):
    quantity: Decimal = Field(..., ge=0, decimal_places=3)

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        logger.trace("Coercing cart decimal value")
        return Decimal(str(v)) if v is not None else v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CartItemTotals(BaseModel):
    item_id: int
    name: str
    sku: str | None
    unit_price: Decimal
    quantity: Decimal
    discount_rate: Decimal
    tax_rate: Decimal
    line_subtotal: Decimal
    line_discount: Decimal
    line_tax: Decimal
    line_total: Decimal


class CartTotals(BaseModel):
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal


class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    item_id: int
    quantity: Decimal
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: int
    desk_number: str | None
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartSummaryResponse(BaseModel):
    cart: CartResponse
    items: list[CartItemTotals]
    totals: CartTotals
