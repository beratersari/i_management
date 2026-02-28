"""
Repository layer for RefreshToken persistence.
All SQL for the `refresh_tokens` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.models.token import RefreshToken

logger = logging.getLogger(__name__)


class TokenRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing TokenRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        logger.trace("Fetching refresh token record")
        row = self._conn.execute(
            "SELECT * FROM refresh_tokens WHERE token = ?", (token,)
        ).fetchone()
        return RefreshToken.from_row(row) if row else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
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

    def revoke(self, token: str) -> bool:
        """Mark a single token as revoked."""
        logger.info("Revoking refresh token")
        cursor = self._conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,)
        )
        logger.info("Refresh token revoke affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0

    def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke every active refresh token for a user (e.g. on logout-all)."""
        logger.info("Revoking all refresh tokens for user id=%s", user_id)
        cursor = self._conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ? AND revoked = 0",
            (user_id,),
        )
        logger.info("Refresh tokens revoked count=%s", cursor.rowcount)
        return cursor.rowcount

    def delete_expired(self) -> int:
        """Housekeeping: remove tokens that have already expired."""
        now = datetime.now(tz=timezone.utc).isoformat()
        logger.info("Deleting expired refresh tokens")
        cursor = self._conn.execute(
            "DELETE FROM refresh_tokens WHERE expires_at < ?", (now,)
        )
        logger.info("Expired refresh tokens deleted=%s", cursor.rowcount)
        return cursor.rowcount
