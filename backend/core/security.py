"""
Security utilities: password hashing and JWT creation/verification.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import logging

from jose import jwt
from passlib.context import CryptContext

from backend.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return the bcrypt hash of *plain_password*."""
    logger.trace("Hashing user password")
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    logger.trace("Verifying password hash")
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _create_token(
    subject: str,
    role: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict] = None,
) -> str:
    """Internal helper that builds and signs a JWT."""
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info("Issued %s token for subject=%s", token_type, subject)
    return token


def create_access_token(user_id: int, role: str) -> str:
    """Create a short-lived access token (15 minutes)."""
    logger.trace("Creating access token for user id=%s", user_id)
    return _create_token(
        subject=str(user_id),
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int, role: str) -> str:
    """Create a long-lived refresh token (7 days)."""
    logger.trace("Creating refresh token for user id=%s", user_id)
    return _create_token(
        subject=str(user_id),
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Raises:
        jose.JWTError: if the token is invalid or expired.
    """
    logger.trace("Decoding JWT token")
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
