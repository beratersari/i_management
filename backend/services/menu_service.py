"""
Menu management service.

Business rules:
- Only authenticated users can add/remove menu items.
- Menu items must reference existing items.
- Duplicate menu entries are rejected.
"""
import sqlite3
import logging

from fastapi import HTTPException, status

from backend.models.menu_item import MenuItem
from backend.models.user import User
from backend.repositories.item_repository import ItemRepository
from backend.repositories.menu_repository import MenuRepository
from backend.schemas.menu import MenuItemCreate

logger = logging.getLogger(__name__)


class MenuService:
    """Business logic for menu item operations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize repositories used by the menu service."""
        logger.trace("Initializing MenuService")
        self._repo = MenuRepository(conn)
        self._item_repo = ItemRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_menu_items(self) -> list[dict]:
        """Return the public menu item list."""
        logger.info("Listing menu items")
        return self._repo.list_public()

    def list_grouped_by_category(self) -> list[dict]:
        """Return public menu items grouped by category."""
        logger.info("Listing menu items grouped by category")
        return self._repo.list_grouped_by_category_public()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add_menu_item(self, data: MenuItemCreate, created_by: User) -> MenuItem:
        """Add an item to the menu after validating it exists."""
        logger.info("Adding menu item item_id=%s", data.item_id)
        item = self._item_repo.get_by_id(data.item_id)
        if not item:
            logger.warning("Item id=%s not found for menu", data.item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id={data.item_id} not found",
            )

        existing = self._repo.get_by_item_id(data.item_id)
        if existing:
            logger.warning("Duplicate menu item for item id=%s", data.item_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Item id={data.item_id} is already on the menu",
            )

        menu_item = self._repo.add(
            item_id=data.item_id,
            display_name=data.display_name,
            description=data.description,
            allergens=data.allergens,
            created_by=created_by.id,
        )
        logger.info("Menu item created id=%s", menu_item.id)
        return menu_item

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def remove_menu_item(self, item_id: int) -> None:
        """Remove an item from the menu and raise 404 if missing."""
        logger.info("Removing menu item item_id=%s", item_id)
        
        # Verify existence first
        existing = self._repo.get_by_item_id(item_id)
        if not existing:
            logger.warning("Menu item not found for item id=%s", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item for item id={item_id} not found",
            )
            
        self._repo.delete(item_id)
        logger.info("Menu item removed item_id=%s", item_id)
