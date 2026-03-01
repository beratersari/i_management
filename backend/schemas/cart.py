"""
Pydantic schemas for Cart request/response validation.
"""
from datetime import datetime
from decimal import Decimal
import logging
from enum import Enum

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class CartStatus(str, Enum):
    """Cart status enumeration."""
    DRAFT = "draft"
    DELETED = "deleted"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CartCreate(BaseModel):
    """Empty payload for creating a cart (user context provides creator)."""


class CartUpdate(BaseModel):
    """Payload for updating cart metadata."""

    desk_number: str | None = Field(
        None,
        min_length=1,
        max_length=20,
        description="Optional desk/table identifier for cafe orders",
    )


class CartStatusUpdate(BaseModel):
    """Payload for updating cart status."""

    status: CartStatus = Field(
        ...,
        description="Cart status: draft, deleted, or completed",
    )


class CartItemCreate(BaseModel):
    """Payload for adding items to a cart."""

    item_id: int = Field(..., gt=0, description="ID of the item to add")
    quantity: Decimal = Field(..., gt=0, decimal_places=3)

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        """Coerce numeric inputs into Decimal values."""
        logger.trace("Coercing cart decimal value")
        return Decimal(str(v)) if v is not None else v


class CartItemUpdate(BaseModel):
    """Payload for updating quantities on cart items."""

    quantity: Decimal = Field(..., ge=0, decimal_places=3)

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        """Coerce numeric inputs into Decimal values."""
        logger.trace("Coercing cart decimal value")
        return Decimal(str(v)) if v is not None else v


class CartItemReturn(BaseModel):
    """Payload for returning items from a cart (partial or full return)."""

    quantity: Decimal | None = Field(
        None,
        gt=0,
        decimal_places=3,
        description="Quantity to return. If not provided, full quantity is returned.",
    )

    @field_validator("quantity", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        """Coerce numeric inputs into Decimal values."""
        logger.trace("Coercing cart decimal value")
        return Decimal(str(v)) if v is not None else v


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CartItemTotals(BaseModel):
    """Line-level totals for a cart item."""

    id: int
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
    """Aggregate totals for a cart."""

    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total: Decimal


class CartItemResponse(BaseModel):
    """Response model for cart items."""

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
    """Response model for cart metadata."""

    id: int
    desk_number: str | None
    status: CartStatus
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartSummaryResponse(BaseModel):
    """Response model that bundles cart items and totals."""

    cart: CartResponse
    items: list[CartItemTotals]
    totals: CartTotals
