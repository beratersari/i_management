"""
Item management endpoints (any authenticated user can access):
  POST   /items                – Create a new item
  GET    /items                – List all items (optionally filter by category)
  GET    /items/search         – Search items by name
  GET    /items/{id}           – Get a specific item
  PATCH  /items/{id}           – Update an item
  DELETE /items/{id}           – Delete an item
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional
import logging

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from backend.services.item_service import ItemService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items", tags=["Items"])


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new item",
)
def create_item(
    data: ItemCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new item. Any authenticated user can create items.
    SKU must be unique across all items.
    """
    logger.info("Creating item %s", data.name)
    service = ItemService(conn)
    return service.create_item(data, created_by=current_user)


@router.get(
    "",
    response_model=list[ItemResponse],
    summary="List all items",
)
def list_items(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Return a list of all items, sorted by name.
    Optionally filter by category_id.
    """
    logger.info("Listing items category_id=%s", category_id)
    service = ItemService(conn)
    return service.list_items(category_id=category_id)


@router.get(
    "/search",
    response_model=list[ItemResponse],
    summary="Search items by name",
)
def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Search items by name (case-insensitive partial match)."""
    logger.info("Searching items query=%s", q)
    service = ItemService(conn)
    return service.search_items(q)


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get a specific item",
)
def get_item(
    item_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Retrieve an item by its ID."""
    logger.info("Fetching item id=%s", item_id)
    service = ItemService(conn)
    return service.get_item(item_id)


@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update an item",
)
def update_item(
    item_id: int,
    data: ItemUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an item's details.
    Any authenticated user can update items.
    """
    logger.info("Updating item id=%s", item_id)
    service = ItemService(conn)
    return service.update_item(item_id, data, updated_by=current_user)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an item",
)
def delete_item(
    item_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Delete an item. Any authenticated user can delete items.
    """
    logger.info("Deleting item id=%s", item_id)
    service = ItemService(conn)
    service.delete_item(item_id)