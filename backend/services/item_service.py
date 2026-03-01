"""
Item management service.
Any authenticated user can create, update, and delete items.
"""
import sqlite3
from typing import Optional
import logging

from fastapi import HTTPException, status

from backend.models.item import Item
from backend.models.user import User
from backend.repositories.item_repository import ItemRepository
from backend.repositories.category_repository import CategoryRepository
from backend.schemas.item import ItemCreate, ItemUpdate

logger = logging.getLogger(__name__)


class ItemService:
    """Business logic for item operations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize repositories used by the item service."""
        logger.trace("Initializing ItemService")
        self._repo = ItemRepository(conn)
        self._category_repo = CategoryRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_item(self, item_id: int) -> Item:
        """Fetch an item by id or raise a 404 HTTP exception."""
        logger.info("Fetching item id=%s", item_id)
        item = self._repo.get_by_id(item_id)
        if not item:
            logger.warning("Item id=%s not found", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id={item_id} not found",
            )
        return item

    def list_items(self, category_id: Optional[int] = None) -> list[Item]:
        """Return items optionally filtered by category id."""
        logger.info("Listing items category_id=%s", category_id)
        return self._repo.list_all(category_id=category_id)

    def search_items(self, query: str) -> list[Item]:
        """Search for items by name using a case-insensitive query."""
        logger.info("Searching items query=%s", query)
        return self._repo.search_by_name(query)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_item(self, data: ItemCreate, created_by: User) -> Item:
        """Create a new item after validating category and SKU rules."""
        logger.info("Creating item %s", data.name)
        # Verify category exists
        category = self._category_repo.get_by_id(data.category_id)
        if not category:
            logger.warning("Category id=%s not found for item", data.category_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id={data.category_id} not found",
            )

        # Check for duplicate SKU (only when one is provided)
        if data.sku is not None:
            existing = self._repo.get_by_sku(data.sku)
            if existing:
                logger.warning("Duplicate item SKU: %s", data.sku)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Item with SKU '{data.sku}' already exists",
                )

        item = self._repo.create(
            category_id=data.category_id,
            name=data.name,
            description=data.description,
            sku=data.sku,
            barcode=data.barcode,
            image_url=data.image_url,
            unit_price=float(data.unit_price),
            unit_type=data.unit_type,
            tax_rate=float(data.tax_rate),
            discount_rate=float(data.discount_rate),
            created_by=created_by.id,
        )
        logger.info("Item created id=%s", item.id)
        return item

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_item(self, item_id: int, data: ItemUpdate, updated_by: User) -> Item:
        """Update an item after validating category and SKU changes."""
        logger.info("Updating item id=%s", item_id)
        item = self.get_item(item_id)

        # Verify new category exists if changing
        if data.category_id is not None and data.category_id != item.category_id:
            category = self._category_repo.get_by_id(data.category_id)
            if not category:
                logger.warning("Category id=%s not found for item update", data.category_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id={data.category_id} not found",
                )

        # Check for SKU conflict if changing
        if data.sku is not None and data.sku != item.sku:
            existing = self._repo.get_by_sku(data.sku)
            if existing:
                logger.warning("Duplicate item SKU update: %s", data.sku)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Item with SKU '{data.sku}' already exists",
                )

        update_fields = {}
        if data.category_id is not None:
            update_fields["category_id"] = data.category_id
        if data.name is not None:
            update_fields["name"] = data.name
        if data.description is not None:
            update_fields["description"] = data.description
        if data.sku is not None:
            update_fields["sku"] = data.sku
        if data.barcode is not None:
            update_fields["barcode"] = data.barcode
        if data.image_url is not None:
            update_fields["image_url"] = data.image_url
        if data.unit_price is not None:
            update_fields["unit_price"] = float(data.unit_price)
        if data.unit_type is not None:
            update_fields["unit_type"] = data.unit_type
        if data.tax_rate is not None:
            update_fields["tax_rate"] = float(data.tax_rate)
        if data.discount_rate is not None:
            update_fields["discount_rate"] = float(data.discount_rate)

        update_fields["updated_by"] = updated_by.id

        updated_item = self._repo.update(item_id, **update_fields)  # type: ignore[return-value]
        logger.info("Item updated id=%s", item_id)
        return updated_item

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_item(self, item_id: int) -> None:
        """Delete an item and raise 404 if it does not exist."""
        logger.info("Deleting item id=%s", item_id)
        if not self._repo.delete(item_id):
            logger.warning("Item id=%s not found for deletion", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id={item_id} not found",
            )
        logger.info("Item deleted id=%s", item_id)