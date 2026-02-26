"""
FastAPI dependency injection helpers for authentication and authorisation.
"""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from backend.core.security import decode_token
from backend.db.database import get_db
from backend.models.user import User, UserRole
from backend.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------

def db_dependency() -> Generator:
    """Yield a database connection for the duration of a request."""
    with get_db() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    conn=Depends(db_dependency),
) -> User:
    """
    Decode the Bearer access token and return the corresponding User.
    Raises HTTP 401 if the token is invalid, expired, or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repo = UserRepository(conn)
    user = repo.get_by_id(int(user_id))
    if user is None or user.is_deleted:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raise HTTP 400 if the account is inactive or soft-deleted."""
    if not current_user.is_active or current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive or deleted user account",
        )
    return current_user


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------

def require_roles(*roles: UserRole):
    """
    Factory that returns a dependency which enforces that the current user
    has one of the specified roles.

    Usage::
        @router.get("/admin-only")
        def admin_only(user: User = Depends(require_roles(UserRole.ADMIN))):
            ...
    """
    def _check(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user
    return _check


# Convenience shortcuts
require_admin = require_roles(UserRole.ADMIN)
require_admin_or_owner = require_roles(UserRole.ADMIN, UserRole.MARKET_OWNER)
