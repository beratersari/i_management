"""
Menu management endpoints:
  POST   /menu                – Add an item to the menu (auth required)
  GET    /menu                – List menu items (public)
  GET    /menu/by-category    – Menu items grouped by category (public)
  DELETE /menu/{item_id}      – Remove an item from the menu (auth required)
"""
from fastapi import APIRouter, Depends, status
import logging

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.menu import (
    MenuItemCreate,
    MenuItemResponse,
    MenuItemPublic,
    MenuCategoryGroupPublic,
)
from backend.services.menu_service import MenuService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.post(
    "",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to the menu",
)
def add_menu_item(
    data: MenuItemCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Add an existing item to the menu (requires authentication)."""
    logger.info("Adding menu item item_id=%s", data.item_id)
    service = MenuService(conn)
    return service.add_menu_item(data, created_by=current_user)


@router.get(
    "",
    response_model=list[MenuItemPublic],
    summary="List menu items",
)
def list_menu_items(
    conn=Depends(db_dependency),
):
    """Return a list of menu items (public)."""
    logger.info("Listing menu items")
    service = MenuService(conn)
    return service.list_menu_items()


@router.get(
    "/by-category",
    response_model=list[MenuCategoryGroupPublic],
    summary="Menu items grouped by category",
)
def list_menu_by_category(
    conn=Depends(db_dependency),
):
    """Return menu items grouped by category (public)."""
    logger.info("Listing menu items grouped by category")
    service = MenuService(conn)
    return service.list_grouped_by_category()


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from the menu",
)
def remove_menu_item(
    item_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Remove an item from the menu (requires authentication)."""
    logger.info("Removing menu item item_id=%s", item_id)
    service = MenuService(conn)
    service.remove_menu_item(item_id)
