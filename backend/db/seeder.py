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


def seed_admin() -> None:
    """
    Insert the default admin user if it does not already exist.
    Safe to call on every startup – it is a no-op when the user is present.
    """
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)
        ).fetchone()

        if existing:
            logger.info("Seeder: admin user '%s' already exists – skipping.", ADMIN_USERNAME)
            return

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
        conn.commit()
        logger.info(
            "Seeder: created default admin user '%s' (email: %s).",
            ADMIN_USERNAME,
            ADMIN_EMAIL,
        )
    finally:
        conn.close()
