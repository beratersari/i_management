"""
Pydantic schemas for token request/response validation.
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Response schema returned after successful login or token refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    """Response schema for access-token-only responses."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT payload (claims) decoded from a token."""

    sub: Optional[str] = None   # user id as string
    role: Optional[str] = None
    type: Optional[str] = None  # "access" | "refresh"


class RefreshTokenRequest(BaseModel):
    """Request body for the /auth/refresh endpoint."""
    refresh_token: str
