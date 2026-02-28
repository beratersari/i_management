"""
Cart management endpoints (any authenticated user can access):
  POST   /carts                          – Create a new cart
  GET    /carts                          – List carts with desk_number
  PATCH  /carts/{cart_id}                – Update cart (e.g., desk_number)
  GET    /carts/{cart_id}                – Get cart summary (items + totals)
  POST   /carts/{cart_id}/items          – Add item to cart
  PATCH  /carts/{cart_id}/items/{id}     – Update cart item quantity
  DELETE /carts/{cart_id}/items          – Clear all items from cart
"""
from fastapi import APIRouter, Depends, status
import logging

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.cart import (
    CartCreate,
    CartUpdate,
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    CartSummaryResponse,
)
from backend.services.cart_service import CartService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cart",
)
def create_cart(
    _: CartCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new cart for the current user."""
    logger.info("Creating cart for user id=%s", current_user.id)
    service = CartService(conn)
    return service.create_cart(created_by=current_user)


@router.get(
    "",
    response_model=list[CartResponse],
    summary="List carts with desk_number",
)
def list_carts_with_desk_number(
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return all carts that have a desk_number assigned."""
    logger.info("Listing carts with desk_number")
    service = CartService(conn)
    return service.list_carts_with_desk_number()


@router.get(
    "/{cart_id}",
    response_model=CartSummaryResponse,
    summary="Get cart summary with totals",
)
def get_cart_summary(
    cart_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return cart items along with pricing totals."""
    logger.info("Fetching cart summary cart_id=%s", cart_id)
    service = CartService(conn)
    return service.calculate_totals(cart_id)


@router.patch(
    "/{cart_id}",
    response_model=CartResponse,
    summary="Update cart (e.g., desk_number)",
)
def update_cart(
    cart_id: int,
    data: CartUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Update cart fields such as desk_number."""
    logger.info("Updating cart cart_id=%s", cart_id)
    service = CartService(conn)
    return service.update_cart(cart_id, data, updated_by=current_user)


@router.post(
    "/{cart_id}/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an item to a cart",
)
def add_cart_item(
    cart_id: int,
    data: CartItemCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add an item to a cart.
    Returns 409 Conflict if the item already exists in the cart.
    Use PATCH to update quantity of existing items.
    """
    logger.info("Adding item to cart cart_id=%s", cart_id)
    service = CartService(conn)
    return service.add_item(cart_id, data, user=current_user)


@router.patch(
    "/{cart_id}/items/{cart_item_id}",
    response_model=CartItemResponse,
    summary="Update a cart item's quantity",
    responses={204: {"description": "Item removed from cart (quantity was 0)"}},
)
def update_cart_item(
    cart_id: int,
    cart_item_id: int,
    data: CartItemUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Update a cart item's quantity (0 removes the item)."""
    logger.info("Updating cart item cart_id=%s cart_item_id=%s", cart_id, cart_item_id)
    service = CartService(conn)
    result = service.update_item(cart_id, cart_item_id, data, user=current_user)
    if result is None:
        from fastapi.responses import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return result


@router.delete(
    "/{cart_id}/items",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear all items from a cart",
)
def clear_cart(
    cart_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Remove all items from a cart."""
    logger.info("Clearing cart cart_id=%s", cart_id)
    service = CartService(conn)
    service.clear_cart(cart_id, user=current_user)
