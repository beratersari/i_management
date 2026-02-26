"""
Pydantic schemas for User request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from backend.models.user import UserRole


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    full_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.EMPLOYEE

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
