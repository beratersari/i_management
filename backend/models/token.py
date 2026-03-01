"""
Domain model representing a stored refresh token row.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshToken:
    id: int
    user_id: int
    token: str
    expires_at: datetime
    revoked: bool
    created_at: datetime

    def __post_init__(self) -> None:
        """Log the creation of the RefreshToken model instance."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Initialized RefreshToken model id=%s", self.id)

    @classmethod
    def from_row(cls, row) -> "RefreshToken":
        """Build a RefreshToken from a sqlite3.Row object."""
        import logging

        logger = logging.getLogger(__name__)
        logger.trace("Hydrating RefreshToken from database row")
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            token=row["token"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            revoked=bool(row["revoked"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
