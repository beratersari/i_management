"""
Repository layer for RefreshToken persistence.
All SQL for the `refresh_tokens` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.token import RefreshToken
from backend.core.logging_config import log_db_timing

logger = logging.getLogger(__name__)


class TokenRepository:
    """Data access layer for refresh token records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Store the database connection for query execution."""
        logger.trace("Initializing TokenRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @log_db_timing
    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Return the refresh token row for the given token string."""
        logger.trace("Fetching refresh token record")
        row = self._conn.execute(
            "SELECT * FROM refresh_tokens WHERE token = ?", (token,)
        ).fetchone()
        return RefreshToken.from_row(row) if row else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @log_db_timing
    def create(self, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
        """Insert a refresh token row and return it."""
        logger.info("Creating refresh token for user id=%s", user_id)
        cursor = self._conn.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, token, expires_at.isoformat()),
        )
        row = self._conn.execute(
            "SELECT * FROM refresh_tokens WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return RefreshToken.from_row(row)

    @log_db_timing
    def revoke(self, token: str) -> bool:
        """Mark a single token as revoked and return True if updated."""
        logger.info("Revoking refresh token")
        cursor = self._conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,)
        )
        logger.info("Refresh token revoke affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0

    @log_db_timing
    def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke all active refresh tokens for a user and return count."""
        logger.info("Revoking all refresh tokens for user id=%s", user_id)
        cursor = self._conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ? AND revoked = 0",
            (user_id,),
        )
        logger.info("Refresh tokens revoked count=%s", cursor.rowcount)
        return cursor.rowcount

    @log_db_timing
    def delete_expired(self) -> int:
        """Delete expired refresh tokens and return the count removed."""
        now = datetime.now(tz=timezone.utc).isoformat()
        logger.info("Deleting expired refresh tokens")
        cursor = self._conn.execute(
            "DELETE FROM refresh_tokens WHERE expires_at < ?", (now,)
        )
        logger.info("Expired refresh tokens deleted=%s", cursor.rowcount)
        return cursor.rowcount
