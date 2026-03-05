"""
Database seeder – creates a default admin account on first startup.

⚠️  FOR DEVELOPMENT ONLY.
    Remove the call to seed_admin() from main.py before deploying to production.

Default credentials:
    username : admin
    password : Admin1234!
    email    : admin@stocktracker.local
"""
import logging

from backend.core.security import hash_password
from backend.db.database import get_connection
from backend.models.user import UserRole

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data – change these values freely during development
# ---------------------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@stocktracker.local"
ADMIN_PASSWORD = "Admin1234!"
ADMIN_FULL_NAME = "Default Admin"

MARKET_OWNER_USERNAME = "owner"
MARKET_OWNER_EMAIL = "owner@stocktracker.local"
MARKET_OWNER_PASSWORD = "Owner1234!"
MARKET_OWNER_FULL_NAME = "Default Market Owner"


def seed_admin() -> None:
    """
    Insert the default admin user and market owner if they do not already exist.
    Safe to call on every startup – it is a no-op when the user is present.
    """
    logger.info("Seeder: ensuring default users")
    conn = get_connection()
    try:
        # Seed Admin
        existing_admin = conn.execute(
            "SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)
        ).fetchone()

        if not existing_admin:
            conn.execute(
                """
                INSERT INTO users (email, username, full_name, hashed_password, role, is_active, is_deleted)
                VALUES (?, ?, ?, ?, ?, 1, 0)
                """,
                (
                    ADMIN_EMAIL,
                    ADMIN_USERNAME,
                    ADMIN_FULL_NAME,
                    hash_password(ADMIN_PASSWORD),
                    UserRole.ADMIN.value,
                ),
            )
            logger.info(
                "Seeder: created default admin user '%s' (email: %s).",
                ADMIN_USERNAME,
                ADMIN_EMAIL,
            )
        
        # Seed Market Owner
        existing_owner = conn.execute(
            "SELECT id FROM users WHERE username = ?", (MARKET_OWNER_USERNAME,)
        ).fetchone()

        if not existing_owner:
            conn.execute(
                """
                INSERT INTO users (email, username, full_name, hashed_password, role, is_active, is_deleted)
                VALUES (?, ?, ?, ?, ?, 1, 0)
                """,
                (
                    MARKET_OWNER_EMAIL,
                    MARKET_OWNER_USERNAME,
                    MARKET_OWNER_FULL_NAME,
                    hash_password(MARKET_OWNER_PASSWORD),
                    UserRole.MARKET_OWNER.value,
                ),
            )
            logger.info(
                "Seeder: created default market owner '%s' (email: %s).",
                MARKET_OWNER_USERNAME,
                MARKET_OWNER_EMAIL,
            )

        conn.commit()
    finally:
        conn.close()
