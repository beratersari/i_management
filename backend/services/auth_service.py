"""
Authentication service: orchestrates login, token refresh, and logout logic.
"""
import sqlite3
from datetime import datetime, timedelta, timezone
import logging

from fastapi import HTTPException, status
from jose import JWTError

from backend.core.config import settings
from backend.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.models.user import User
from backend.repositories.user_repository import UserRepository
from backend.repositories.token_repository import TokenRepository
from backend.schemas.token import Token, AccessToken

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing AuthService")
        self._user_repo = UserRepository(conn)
        self._token_repo = TokenRepository(conn)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> Token:
        """
        Validate credentials and issue a new access + refresh token pair.
        Accepts either username or email in the *username* field.
        """
        logger.info("Authenticating user '%s'", username)
        user = (
            self._user_repo.get_by_username(username)
            or self._user_repo.get_by_email(username)
        )

        if not user or not verify_password(password, user.hashed_password):
            logger.warning("Invalid login attempt for '%s'", username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning("Inactive user attempted login id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account",
            )

        logger.info("Login successful for user id=%s", user.id)
        return self._issue_token_pair(user)

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------

    def refresh(self, refresh_token_str: str) -> AccessToken:
        """
        Validate the refresh token and issue a new access token.
        The refresh token is NOT rotated here (single-use rotation can be
        added later by revoking the old token and issuing a new one).
        """
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

        # 1. Verify JWT signature & expiry
        try:
            payload = decode_token(refresh_token_str)
        except JWTError:
            logger.warning("Refresh token decode failed")
            raise invalid_exc

        if payload.get("type") != "refresh":
            logger.warning("Refresh token type mismatch")
            raise invalid_exc

        # 2. Check the token exists in the DB and is not revoked
        stored = self._token_repo.get_by_token(refresh_token_str)
        if stored is None or stored.revoked:
            logger.warning("Refresh token revoked or missing")
            raise invalid_exc

        # 3. Check DB-level expiry (belt-and-suspenders)
        if stored.expires_at < datetime.now(tz=timezone.utc):
            logger.warning("Refresh token expired in database")
            raise invalid_exc

        # 4. Fetch the user
        user_id = int(payload["sub"])
        user = self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            logger.warning("Refresh token user not found or inactive")
            raise invalid_exc

        logger.info("Refresh token validated for user id=%s", user.id)
        access_token = create_access_token(user.id, user.role.value)
        return AccessToken(access_token=access_token)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def logout(self, refresh_token_str: str) -> None:
        """Revoke the provided refresh token."""
        revoked = self._token_repo.revoke(refresh_token_str)
        logger.info("Refresh token revoked=%s", revoked)

    def logout_all(self, user_id: int) -> None:
        """Revoke every refresh token belonging to *user_id*."""
        count = self._token_repo.revoke_all_for_user(user_id)
        logger.info("Revoked %s refresh tokens for user id=%s", count, user_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _issue_token_pair(self, user: User) -> Token:
        access_token = create_access_token(user.id, user.role.value)
        refresh_token_str = create_refresh_token(user.id, user.role.value)

        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        self._token_repo.create(user.id, refresh_token_str, expires_at)
        logger.info("Issued token pair for user id=%s", user.id)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
        )
