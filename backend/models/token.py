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

    @classmethod
    def from_row(cls, row) -> "RefreshToken":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            token=row["token"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            revoked=bool(row["revoked"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
