"""
Repository layer for User persistence.
All SQL for the `users` table lives here.
"""
import sqlite3
from typing import Optional
from datetime import datetime, timezone
import logging

from backend.models.user import User, UserRole
from backend.core.logging_config import log_db_timing

logger = logging.getLogger(__name__)


class UserRepository:
    """Data access layer for user records."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Store the database connection for query execution."""
        logger.trace("Initializing UserRepository")
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @log_db_timing
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Return a user by id or None if missing."""
        logger.trace("Fetching user by id=%s", user_id)
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User.from_row(row) if row else None

    @log_db_timing
    def get_active_by_id(self, user_id: int) -> Optional[User]:
        """Return a user only if they are not soft-deleted."""
        logger.trace("Fetching active user by id=%s", user_id)
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ? AND is_deleted = 0", (user_id,)
        ).fetchone()
        return User.from_row(row) if row else None

    @log_db_timing
    def get_by_email(self, email: str) -> Optional[User]:
        """Return a non-deleted user by email."""
        logger.trace("Fetching user by email=%s", email)
        row = self._conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_deleted = 0", (email,)
        ).fetchone()
        return User.from_row(row) if row else None

    @log_db_timing
    def get_by_username(self, username: str) -> Optional[User]:
        """Return a non-deleted user by username."""
        logger.trace("Fetching user by username=%s", username)
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_deleted = 0", (username,)
        ).fetchone()
        return User.from_row(row) if row else None

    @log_db_timing
    def list_all(self, include_deleted: bool = False) -> list[User]:
        """Return users, optionally including soft-deleted accounts."""
        logger.trace("Listing users include_deleted=%s", include_deleted)
        if include_deleted:
            rows = self._conn.execute("SELECT * FROM users").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM users WHERE is_deleted = 0"
            ).fetchall()
        return [User.from_row(r) for r in rows]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @log_db_timing
    def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        role: UserRole,
        full_name: Optional[str] = None,
    ) -> User:
        """Insert a new user row and return the created user."""
        logger.info("Creating user record username=%s", username)
        cursor = self._conn.execute(
            """
            INSERT INTO users (email, username, full_name, hashed_password, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, username, full_name, hashed_password, role.value),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    @log_db_timing
    def update(self, user_id: int, **fields) -> Optional[User]:
        """Update user fields and return the updated row."""
        if not fields:
            logger.trace("No user fields to update id=%s", user_id)
            return self.get_by_id(user_id)

        logger.info("Updating user record id=%s", user_id)
        fields["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [user_id]
        self._conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?", values
        )
        return self.get_by_id(user_id)

    @log_db_timing
    def soft_delete(self, user_id: int) -> bool:
        """
        Mark the user as deleted without removing the row.
        Also deactivates the account and records the deletion timestamp.
        """
        logger.info("Soft deleting user id=%s", user_id)
        now = datetime.now(tz=timezone.utc).isoformat()
        cursor = self._conn.execute(
            """
            UPDATE users
            SET is_deleted = 1,
                is_active  = 0,
                deleted_at = ?,
                updated_at = ?
            WHERE id = ? AND is_deleted = 0
            """,
            (now, now, user_id),
        )
        logger.info("Soft delete affected %s rows", cursor.rowcount)
        return cursor.rowcount > 0
