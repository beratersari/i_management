"""
Central v1 API router – registers all endpoint sub-routers.
"""
from fastapi import APIRouter

from backend.api.v1.endpoints import auth, users, categories, items, stock

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(items.router)
api_router.include_router(stock.router)
