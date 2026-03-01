"""
Stock management service.

Business rules:
  - An item must exist before it can be added to stock.
  - Each item can only have ONE stock entry (no duplicates).
  - Quantity can be updated at any time via a separate endpoint.
  - Any authenticated user can manage stock entries.
"""
import sqlite3
import logging

from fastapi import HTTPException, status

from backend.models.stock import StockEntry
from backend.models.user import User
from backend.repositories.item_repository import ItemRepository
from backend.repositories.stock_repository import StockRepository
from backend.schemas.stock import StockCreate, StockUpdate

logger = logging.getLogger(__name__)


class StockService:
    """Business logic for stock management."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize repositories used by the stock service."""
        logger.trace("Initializing StockService")
        self._repo = StockRepository(conn)
        self._item_repo = ItemRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_entry(self, item_id: int) -> StockEntry:
        """Return the stock entry for an item, or 404 if not yet stocked."""
        logger.info("Fetching stock entry item_id=%s", item_id)
        entry = self._repo.get_by_item_id(item_id)
        if not entry:
            logger.warning("Stock entry not found for item id=%s", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stock entry found for item id={item_id}",
            )
        return entry

    def list_entries(self) -> list[StockEntry]:
        """Return all stock entries ordered by item id."""
        logger.info("Listing stock entries")
        return self._repo.list_all()

    def list_grouped_by_category(self) -> list[dict]:
        """Return stocked items grouped by category."""
        logger.info("Listing stock grouped by category")
        return self._repo.list_grouped_by_category()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def add_to_stock(self, data: StockCreate, created_by: User) -> StockEntry:
        """Add an item to stock after validating existence and uniqueness."""
        logger.info("Adding item to stock item_id=%s", data.item_id)
        # Verify the item exists
        item = self._item_repo.get_by_id(data.item_id)
        if not item:
            logger.warning("Item id=%s not found for stock", data.item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id={data.item_id} not found",
            )

        # Reject duplicates
        existing = self._repo.get_by_item_id(data.item_id)
        if existing:
            logger.warning("Duplicate stock entry for item id=%s", data.item_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Item id={data.item_id} is already in stock "
                    f"(stock entry id={existing.id}). "
                    "Use PATCH /stock/{item_id} to update the quantity."
                ),
            )

        entry = self._repo.add(
            item_id=data.item_id,
            quantity=float(data.quantity),
            created_by=created_by.id,
        )
        logger.info("Stock entry created id=%s", entry.id)
        return entry

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_quantity(
        self, item_id: int, data: StockUpdate, updated_by: User
    ) -> StockEntry:
        """Update the quantity for a stocked item after validation."""
        logger.info("Updating stock entry item_id=%s", item_id)
        # Ensure the entry exists (raises 404 if not)
        self.get_entry(item_id)

        updated_entry = self._repo.update_quantity(  # type: ignore[return-value]
            item_id=item_id,
            quantity=float(data.quantity),
            updated_by=updated_by.id,
        )
        logger.info("Stock entry updated item_id=%s", item_id)
        return updated_entry

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def remove_from_stock(self, item_id: int) -> None:
        """Remove a stock entry and raise 404 if missing."""
        logger.info("Removing stock entry item_id=%s", item_id)
        if not self._repo.delete(item_id):
            logger.warning("Stock entry not found for item id=%s", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stock entry found for item id={item_id}",
            )
        logger.info("Stock entry removed item_id=%s", item_id)
