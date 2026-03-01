"""
Pydantic schemas for Item request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ItemCreate(BaseModel):
    """Payload for creating items."""

    category_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    unit_type: str = Field(default="piece", max_length=20)
    tax_rate: Decimal = Field(default=0, ge=0, le=100, decimal_places=2)
    discount_rate: Decimal = Field(default=0, ge=0, le=100, decimal_places=2)

    @field_validator("unit_price", "tax_rate", "discount_rate", mode="before")
    @classmethod
    def validate_decimal(cls, v):
        """Normalize decimal inputs to Decimal instances."""
        logger.trace("Validating item decimal value")
        if v is None:
            return v
        return Decimal(str(v))


class ItemUpdate(BaseModel):
    """Payload for updating items."""

    category_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    barcode: Optional[str] = Field(None, max_length=50)
    image_url: Optional[str] = Field(None, max_length=500)
    unit_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    unit_type: Optional[str] = Field(None, max_length=20)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)

    @field_validator("unit_price", "tax_rate", "discount_rate", mode="before")
    @classmethod
    def validate_decimal(cls, v):
        """Normalize decimal inputs to Decimal instances."""
        logger.trace("Validating item decimal value")
        if v is None:
            return v
        return Decimal(str(v))


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ItemResponse(BaseModel):
    """Response model for item data."""

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

    model_config = {"from_attributes": True}