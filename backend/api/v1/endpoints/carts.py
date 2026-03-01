"""
Cart management endpoints (any authenticated user can access):
  POST   /carts                          – Create a new cart
  GET    /carts                          – List carts with desk_number
  PATCH  /carts/{cart_id}                – Update cart (e.g., desk_number)
  GET    /carts/{cart_id}                – Get cart summary (items + totals)
  POST   /carts/{cart_id}/complete       – Mark cart as completed
  POST   /carts/{cart_id}/delete         – Mark cart as deleted
  POST   /carts/{cart_id}/items          – Add item to cart
  PATCH  /carts/{cart_id}/items/{id}     – Update cart item quantity
  DELETE /carts/{cart_id}/items          – Clear all items from cart
  GET    /carts/sales/report             – Export sales report as PDF
"""
from datetime import date, timedelta
from io import BytesIO

from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import StreamingResponse
import logging

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.cart import (
    CartCreate,
    CartUpdate,
    CartItemCreate,
    CartItemReturn,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    CartSummaryResponse,
    CartStatus,
)
from backend.services.cart_service import CartService
from backend.services.pdf_service import PDFService

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
    "/{cart_id}/complete",
    response_model=CartResponse,
    summary="Mark cart as completed",
)
def complete_cart(
    cart_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a cart as completed. Completed carts cannot be modified."""
    logger.info("Completing cart cart_id=%s", cart_id)
    service = CartService(conn)
    return service.complete_cart(cart_id, updated_by=current_user)


@router.post(
    "/{cart_id}/delete",
    response_model=CartResponse,
    summary="Mark cart as deleted",
)
def delete_cart(
    cart_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a cart as deleted (soft delete). Deleted carts cannot be modified."""
    logger.info("Deleting cart cart_id=%s", cart_id)
    service = CartService(conn)
    return service.delete_cart(cart_id, updated_by=current_user)


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


@router.post(
    "/{cart_id}/items/{cart_item_id}/return",
    response_model=CartItemResponse,
    summary="Return a cart item (partial or full return)",
    responses={
        204: {"description": "Item fully returned and removed from cart"},
        200: {"description": "Item partially returned, updated cart item returned"},
    },
)
def return_cart_item(
    cart_id: int,
    cart_item_id: int,
    data: CartItemReturn = CartItemReturn(),
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return a cart item (partial or full return).
    
    - If `quantity` is not provided in the body, performs a **full return** (removes item from cart).
    - If `quantity` is provided, performs a **partial return** (reduces quantity).
    
    Returns:
    - 204 No Content if the item was fully returned and removed.
    - 200 OK with the updated CartItem if partially returned.
    """
    logger.info("Returning cart item cart_id=%s cart_item_id=%s", cart_id, cart_item_id)
    service = CartService(conn)
    result = service.return_item(cart_id, cart_item_id, data, user=current_user)
    if result is None:
        from fastapi.responses import Response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return result


@router.get(
    "/sales/report/pdf",
    summary="Export sales report as PDF",
    response_class=StreamingResponse,
)
def export_sales_pdf(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Export a sales report as PDF for the given date range.
    Includes all completed carts with their totals in a table format.
    """
    logger.info("Exporting sales PDF from %s to %s", start_date, end_date)
    
    # Adjust end_date to include the full day
    end_date_adjusted = end_date + timedelta(days=1)
    
    cart_service = CartService(conn)
    sales_data = cart_service.get_sales_report(
        start_date.isoformat(), 
        end_date_adjusted.isoformat()
    )
    
    pdf_service = PDFService()
    pdf_buffer = pdf_service.generate_sales_report(
        sales_data, 
        start_date, 
        end_date
    )
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=sales_report_{start_date}_{end_date}.pdf"
        },
    )
