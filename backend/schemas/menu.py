"""
Pydantic schemas for MenuItem request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class MenuItemCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="Existing item ID to add to the menu")
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    allergens: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class MenuItemResponse(BaseModel):
    id: int
    item_id: int
    display_name: str
    description: Optional[str]
    allergens: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MenuItemPublic(BaseModel):
    display_name: str
    image_url: Optional[str]
    description: Optional[str]
    unit_price: Decimal
    allergens: Optional[str]
    discount_rate: Decimal


class MenuCategoryGroupPublic(BaseModel):
    category_id: int
    category_name: str
    sort_order: int
    items: list[MenuItemPublic]
