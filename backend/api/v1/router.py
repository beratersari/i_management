"""
Central v1 API router – registers all endpoint sub-routers.
"""
from fastapi import APIRouter
import logging

from backend.api.v1.endpoints import auth, users, categories, items, stock, carts, daily_accounts, time_entries, menu

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api/v1")

logger.info("Registering v1 API routers")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(items.router)
api_router.include_router(stock.router)
api_router.include_router(menu.router)
api_router.include_router(carts.router)
api_router.include_router(daily_accounts.router)
api_router.include_router(time_entries.router)
