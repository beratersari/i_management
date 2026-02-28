"""
Stock management endpoints (any authenticated user can access):
  POST   /stock                        – Add an item to stock
  GET    /stock                        – List all stock entries
  GET    /stock/by-category            – Stock grouped by category (sorted by name)
  GET    /stock/{item_id}              – Get stock entry for a specific item
  PATCH  /stock/{item_id}              – Update quantity for a stocked item
  DELETE /stock/{item_id}              – Remove an item from stock
"""
from fastapi import APIRouter, Depends, status
import logging

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.stock import (
    StockCreate,
    StockUpdate,
    StockEntryResponse,
    StockCategoryGroup,
)
from backend.services.stock_service import StockService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.post(
    "",
    response_model=StockEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to stock",
)
def add_to_stock(
    data: StockCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add a previously created item to stock with an initial quantity.

    - Each item can only be added once (duplicate `item_id` → **409 Conflict**).
    - To change the quantity later, use **PATCH /stock/{item_id}**.
    """
    logger.info("Adding item to stock item_id=%s", data.item_id)
    service = StockService(conn)
    return service.add_to_stock(data, created_by=current_user)


@router.get(
    "",
    response_model=list[StockEntryResponse],
    summary="List all stock entries",
)
def list_stock(
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return a flat list of all stock entries ordered by item_id."""
    logger.info("Listing stock entries")
    service = StockService(conn)
    return service.list_entries()


@router.get(
    "/by-category",
    response_model=list[StockCategoryGroup],
    summary="Stock grouped by category",
)
def list_stock_by_category(
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Return all stocked items grouped by their category.
    Within each category, items are sorted alphabetically by name.
    """
    logger.info("Listing stock grouped by category")
    service = StockService(conn)
    return service.list_grouped_by_category()


@router.get(
    "/{item_id}",
    response_model=StockEntryResponse,
    summary="Get stock entry for an item",
)
def get_stock_entry(
    item_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Retrieve the stock entry for the given item ID."""
    logger.info("Fetching stock entry item_id=%s", item_id)
    service = StockService(conn)
    return service.get_entry(item_id)


@router.patch(
    "/{item_id}",
    response_model=StockEntryResponse,
    summary="Update stock quantity for an item",
)
def update_stock(
    item_id: int,
    data: StockUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update the quantity on hand for a stocked item.
    The item must already have a stock entry (use **POST /stock** to create one first).
    """
    logger.info("Updating stock entry item_id=%s", item_id)
    service = StockService(conn)
    return service.update_quantity(item_id, data, updated_by=current_user)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an item from stock",
)
def remove_from_stock(
    item_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Remove the stock entry for the given item entirely."""
    logger.info("Removing stock entry item_id=%s", item_id)
    service = StockService(conn)
    service.remove_from_stock(item_id)
