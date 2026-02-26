"""
Pydantic schemas for Category request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: int
    updated_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}