"""
Repository layer for RefreshToken persistence.
All SQL for the `refresh_tokens` table lives here.
"""
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from backend.models.token import RefreshToken


class TokenRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        row = self._conn.execute(
            "SELECT * FROM refresh_tokens WHERE token = ?", (token,)
        ).fetchone()
        return RefreshToken.from_row(row) if row else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(self, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
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
        cursor = self._conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE token = ?", (token,)
        )
        return cursor.rowcount > 0

    def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke every active refresh token for a user (e.g. on logout-all)."""
        cursor = self._conn.execute(
            "UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ? AND revoked = 0",
            (user_id,),
        )
        return cursor.rowcount

    def delete_expired(self) -> int:
        """Housekeeping: remove tokens that have already expired."""
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            "DELETE FROM refresh_tokens WHERE expires_at < ?", (now,)
        )
        return cursor.rowcount
