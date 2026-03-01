"""
Application entry point.
Run with:  uvicorn backend.main:app --reload

⚠️  DEVELOPMENT NOTE:
    A default admin user is seeded automatically on startup (see backend/db/seeder.py).
    Remove the seed_admin() call below before deploying to production.
"""
import logging

from fastapi import FastAPI

from backend.core.logging_config import configure_logging
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.api.v1.router import api_router
from backend.db.database import init_db
from backend.db.seeder import seed_admin
from backend.db.mock_seeder import seed_mock_data

configure_logging()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    logger = logging.getLogger(__name__)
    logger.info("Starting FastAPI application setup")
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Backend API for a stock and order tracking application "
            "designed for cafes and greengrocers."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ──────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Startup / shutdown events ───────────────────────────────────────────
    @app.on_event("startup")
    def on_startup() -> None:
        """Initialize the database and development seed data."""
        logger.info("Initializing database and seed data")
        init_db()
        # ⚠️ DEV ONLY – remove these seeders before going to production
        seed_admin()
        seed_mock_data()

    return app


app = create_app()
