"""
Repository layer for User persistence.
All SQL for the `users` table lives here.
"""
import sqlite3
from typing import Optional
from datetime import datetime, timezone

from backend.models.user import User, UserRole


class UserRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Return a user regardless of deleted status (used internally)."""
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User.from_row(row) if row else None

    def get_active_by_id(self, user_id: int) -> Optional[User]:
        """Return a user only if they are not soft-deleted."""
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ? AND is_deleted = 0", (user_id,)
        ).fetchone()
        return User.from_row(row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        """Return a non-deleted user by email."""
        row = self._conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_deleted = 0", (email,)
        ).fetchone()
        return User.from_row(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:
        """Return a non-deleted user by username."""
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_deleted = 0", (username,)
        ).fetchone()
        return User.from_row(row) if row else None

    def list_all(self, include_deleted: bool = False) -> list[User]:
        """List users; by default only non-deleted users are returned."""
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

    def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        role: UserRole,
        full_name: Optional[str] = None,
    ) -> User:
        cursor = self._conn.execute(
            """
            INSERT INTO users (email, username, full_name, hashed_password, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, username, full_name, hashed_password, role.value),
        )
        return self.get_by_id(cursor.lastrowid)  # type: ignore[return-value]

    def update(self, user_id: int, **fields) -> Optional[User]:
        """
        Update arbitrary columns on a user row.
        Only non-None values in *fields* are applied.
        """
        if not fields:
            return self.get_by_id(user_id)

        fields["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        set_clause = ", ".join(f"{col} = ?" for col in fields)
        values = list(fields.values()) + [user_id]
        self._conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?", values
        )
        return self.get_by_id(user_id)

    def soft_delete(self, user_id: int) -> bool:
        """
        Mark the user as deleted without removing the row.
        Also deactivates the account and records the deletion timestamp.
        """
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
        return cursor.rowcount > 0
