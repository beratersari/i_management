"""
Cart management service.
Store employees can create carts, add/update items, clear carts, and view totals.
"""
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
import logging

from fastapi import HTTPException, status

from backend.models.cart import Cart, CartStatus
from backend.models.cart_item import CartItem
from backend.models.item import Item
from backend.models.stock import StockEntry
from backend.models.user import User
from backend.repositories.cart_repository import CartRepository
from backend.repositories.item_repository import ItemRepository
from backend.repositories.stock_repository import StockRepository
from backend.schemas.cart import CartItemCreate, CartItemReturn, CartItemUpdate, CartUpdate, CartStatus

logger = logging.getLogger(__name__)


class CartService:
    """Business logic for cart creation, updates, and totals."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize repositories used by the cart service."""
        logger.trace("Initializing CartService")
        self._conn = conn
        self._cart_repo = CartRepository(conn)
        self._item_repo = ItemRepository(conn)
        self._stock_repo = StockRepository(conn)

    # ------------------------------------------------------------------
    # Cart lifecycle
    # ------------------------------------------------------------------

    def create_cart(self, created_by: User) -> Cart:
        """Create a new cart owned by the requesting user."""
        logger.info("Creating cart for user id=%s", created_by.id)
        cart = self._cart_repo.create(created_by=created_by.id)
        logger.info("Cart created id=%s", cart.id)
        return cart

    def get_cart(self, cart_id: int) -> Cart:
        """Fetch a cart by id or raise a 404 HTTP exception."""
        logger.info("Fetching cart id=%s", cart_id)
        cart = self._cart_repo.get_by_id(cart_id)
        if not cart:
            logger.warning("Cart id=%s not found", cart_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart with id={cart_id} not found",
            )
        return cart

    def _ensure_cart_editable(self, cart: Cart) -> None:
        """Raise an error if the cart is not in draft status."""
        if cart.status != CartStatus.DRAFT:
            logger.warning("Cart id=%s is not editable (status=%s)", cart.id, cart.status.value)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cart is not editable (status={cart.status.value}). Only draft carts can be modified.",
            )

    def update_cart_status(self, cart_id: int, status: CartStatus, updated_by: User) -> Cart:
        """Update the status of a cart."""
        logger.info("Updating cart id=%s status to %s", cart_id, status.value)
        cart = self.get_cart(cart_id)
        
        # Validate status transitions
        if cart.status == CartStatus.COMPLETED and status != CartStatus.COMPLETED:
            logger.warning("Cannot change status of completed cart id=%s", cart_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot change status of a completed cart",
            )
        
        if cart.status == CartStatus.DELETED and status != CartStatus.DELETED:
            logger.warning("Cannot change status of deleted cart id=%s", cart_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot change status of a deleted cart",
            )
        
        updated = self._cart_repo.update_status(cart.id, status, updated_by.id)
        if not updated:
            logger.warning("Cart id=%s not found for status update", cart_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart with id={cart_id} not found",
            )
        logger.info("Cart id=%s status updated to %s", cart_id, status.value)
        return updated

    def complete_cart(self, cart_id: int, updated_by: User) -> Cart:
        """Mark a cart as completed."""
        return self.update_cart_status(cart_id, CartStatus.COMPLETED, updated_by)

    def delete_cart(self, cart_id: int, updated_by: User) -> Cart:
        """Mark a cart as deleted (soft delete)."""
        return self.update_cart_status(cart_id, CartStatus.DELETED, updated_by)

    def get_sales_report(self, start_date: str, end_date: str) -> list[dict]:
        """Get a sales report for the given date range."""
        logger.info("Generating sales report from %s to %s", start_date, end_date)
        return self._cart_repo.list_completed_by_date_range(start_date, end_date)

    # ------------------------------------------------------------------
    # Cart item management
    # ------------------------------------------------------------------

    def add_item(self, cart_id: int, data: CartItemCreate, user: User) -> CartItem:
        """Add an item to a cart and ensure it is unique."""
        logger.info("Adding item id=%s to cart id=%s", data.item_id, cart_id)
        cart = self.get_cart(cart_id)
        self._ensure_cart_editable(cart)
        item = self._get_item(data.item_id)
        stock = self._get_stock(item.id)

        existing = self._cart_repo.get_cart_item_by_cart_and_item(cart.id, item.id)
        if existing:
            logger.warning("Item id=%s already in cart id=%s", item.id, cart.id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Item id={item.id} already exists in cart. "
                    f"Use PATCH /carts/{cart.id}/items/{existing.id} to update quantity."
                ),
            )

        self._ensure_stock_available(stock, data.quantity)

        created = self._cart_repo.create_cart_item(
            cart_id=cart.id,
            item_id=item.id,
            quantity=float(data.quantity),
            created_by=user.id,
        )
        # Decrement stock
        self._stock_repo.adjust_quantity(item.id, -float(data.quantity), user.id)

        self._cart_repo.touch(cart.id, user.id)
        logger.info("Cart item added id=%s", created.id)
        return created

    def update_item(
        self, cart_id: int, cart_item_id: int, data: CartItemUpdate, user: User
    ) -> CartItem | None:
        """Update a cart item's quantity or delete when quantity is zero."""
        logger.info("Updating cart item id=%s in cart id=%s", cart_item_id, cart_id)
        cart = self.get_cart(cart_id)
        self._ensure_cart_editable(cart)
        cart_item = self._get_cart_item(cart.id, cart_item_id)

        if data.quantity == 0:
            # Increment stock back
            self._stock_repo.adjust_quantity(cart_item.item_id, float(cart_item.quantity), user.id)
            self._cart_repo.delete_cart_item(cart_item.id)
            self._cart_repo.touch(cart.id, user.id)
            logger.info("Cart item removed id=%s", cart_item.id)
            return None

        # Calculate delta
        delta = data.quantity - cart_item.quantity
        if delta > 0:
            stock = self._get_stock(cart_item.item_id)
            self._ensure_stock_available(stock, delta)

        updated = self._cart_repo.update_cart_item_quantity(
            cart_item.id, data.quantity, updated_by=user.id
        )
        # Adjust stock
        self._stock_repo.adjust_quantity(cart_item.item_id, -float(delta), user.id)

        self._cart_repo.touch(cart.id, user.id)
        logger.info("Cart item updated id=%s", cart_item.id)
        return updated  # type: ignore[return-value]

    def clear_cart(self, cart_id: int, user: User) -> int:
        """Remove all cart items for the given cart and increment stock."""
        logger.info("Clearing cart id=%s", cart_id)
        cart = self.get_cart(cart_id)
        self._ensure_cart_editable(cart)
        cart_items = self._cart_repo.list_cart_items_by_cart(cart.id)
        
        for ci in cart_items:
            self._stock_repo.adjust_quantity(ci.item_id, float(ci.quantity), user.id)

        cleared = self._cart_repo.clear_cart_items(cart.id)
        self._cart_repo.touch(cart.id, user.id)
        logger.info("Cleared %s items from cart id=%s", cleared, cart.id)
        return cleared

    def return_item(
        self, cart_id: int, cart_item_id: int, data: CartItemReturn, user: User
    ) -> CartItem | None:
        """
        Return a cart item (partial or full return).
        
        If quantity is not provided, performs a full return.
        If quantity is provided, performs a partial return and updates the cart item.
        Returns None if the item was fully removed, or the updated CartItem if partial.
        """
        logger.info(
            "Returning cart item id=%s from cart id=%s (quantity=%s)",
            cart_item_id,
            cart_id,
            data.quantity,
        )
        
        # Validate cart exists first
        cart = self.get_cart(cart_id)
        self._ensure_cart_editable(cart)
        
        # Validate cart item exists and belongs to the cart
        cart_item = self._cart_repo.get_cart_item_by_id(cart_item_id)
        if not cart_item:
            logger.warning("Cart item id=%s not found", cart_item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item with id={cart_item_id} not found",
            )
        
        if cart_item.cart_id != cart_id:
            logger.warning(
                "Cart item id=%s does not belong to cart id=%s",
                cart_item_id,
                cart_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item with id={cart_item_id} not found in cart {cart_id}",
            )
        
        # Determine return quantity
        return_quantity = data.quantity if data.quantity is not None else cart_item.quantity
        
        # Validate return quantity
        if return_quantity <= Decimal("0"):
            logger.warning("Invalid return quantity: %s", return_quantity)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Return quantity must be greater than 0",
            )
        
        if return_quantity > cart_item.quantity:
            logger.warning(
                "Cannot return more than available (requested: %s, available: %s)",
                return_quantity,
                cart_item.quantity,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot return {return_quantity} when only {cart_item.quantity} is in cart",
            )
        
        # Increment stock
        self._stock_repo.adjust_quantity(
            cart_item.item_id, float(return_quantity), user.id
        )
        
        # Calculate new quantity
        new_quantity = cart_item.quantity - return_quantity
        
        if new_quantity == Decimal("0"):
            # Full return - delete the cart item
            self._cart_repo.delete_cart_item(cart_item.id)
            self._cart_repo.touch(cart.id, user.id)
            logger.info("Cart item fully returned and removed id=%s", cart_item.id)
            return None
        else:
            # Partial return - update the cart item quantity
            updated = self._cart_repo.update_cart_item_quantity(
                cart_item.id, new_quantity, updated_by=user.id
            )
            self._cart_repo.touch(cart.id, user.id)
            logger.info(
                "Cart item partially returned id=%s, new quantity=%s",
                cart_item.id,
                new_quantity,
            )
            return updated  # type: ignore[return-value]

    def list_cart_items(self, cart_id: int) -> list[CartItem]:
        """List all items currently in a cart."""
        logger.info("Listing items for cart id=%s", cart_id)
        cart = self.get_cart(cart_id)
        return self._cart_repo.list_cart_items_by_cart(cart.id)

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------

    def calculate_totals(self, cart_id: int) -> dict:
        """Calculate pricing totals and line items for a cart."""
        logger.info("Calculating totals for cart id=%s", cart_id)
        cart = self.get_cart(cart_id)
        cart_items = self._cart_repo.list_cart_items_by_cart(cart.id)
        if not cart_items:
            logger.info("Cart id=%s has no items", cart.id)
            return {
                "cart": cart,
                "items": [],
                "totals": self._empty_totals(),
            }

        item_map = {item.id: item for item in self._list_items(cart_items)}
        line_items = []
        subtotal = Decimal("0")
        discount_total = Decimal("0")
        tax_total = Decimal("0")

        for cart_item in cart_items:
            item = item_map.get(cart_item.item_id)
            if not item:
                logger.warning("Missing item id=%s for cart totals", cart_item.item_id)
                continue

            line = self._calculate_line(item, cart_item.quantity)
            line_items.append({
                "id": cart_item.id,
                "item_id": item.id,
                "name": item.name,
                "sku": item.sku,
                "unit_price": item.unit_price,
                "quantity": cart_item.quantity,
                "discount_rate": item.discount_rate,
                "tax_rate": item.tax_rate,
                "line_subtotal": line["line_subtotal"],
                "line_discount": line["line_discount"],
                "line_tax": line["line_tax"],
                "line_total": line["line_total"],
            })
            subtotal += line["line_subtotal"]
            discount_total += line["line_discount"]
            tax_total += line["line_tax"]

        total = subtotal - discount_total + tax_total
        totals = {
            "subtotal": self._money(subtotal),
            "discount_total": self._money(discount_total),
            "tax_total": self._money(tax_total),
            "total": self._money(total),
        }
        logger.info("Totals calculated for cart id=%s", cart.id)
        return {
            "cart": cart,
            "items": line_items,
            "totals": totals,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_item(self, item_id: int) -> Item:
        """Fetch an item or raise if it is missing."""
        logger.trace("Fetching item id=%s for cart", item_id)
        item = self._item_repo.get_by_id(item_id)
        if not item:
            logger.warning("Item id=%s not found for cart", item_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id={item_id} not found",
            )
        return item

    def _get_stock(self, item_id: int) -> StockEntry:
        """Fetch stock for an item or raise if unavailable."""
        logger.trace("Fetching stock for item id=%s", item_id)
        stock = self._stock_repo.get_by_item_id(item_id)
        if not stock:
            logger.warning("Item id=%s not in stock", item_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Item id={item_id} is not in stock. "
                    "Add it to stock before adding to a cart."
                ),
            )
        return stock

    def _ensure_stock_available(self, stock: StockEntry, desired_quantity: Decimal) -> None:
        """Raise an HTTP conflict if the desired quantity exceeds stock."""
        if desired_quantity > stock.quantity:
            logger.warning(
                "Requested quantity exceeds available stock (%s > %s)",
                desired_quantity,
                stock.quantity,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Requested quantity exceeds available stock "
                    f"({desired_quantity} > {stock.quantity})."
                ),
            )

    def _get_cart_item(self, cart_id: int, cart_item_id: int) -> CartItem:
        """Return a cart item ensuring it belongs to the given cart."""
        cart_item = self._cart_repo.get_cart_item_by_id(cart_item_id)
        if cart_item and cart_item.cart_id == cart_id:
            return cart_item

        cart_item = self._cart_repo.get_cart_item_by_cart_and_item(cart_id, cart_item_id)
        if not cart_item:
            logger.warning("Cart item id=%s not found in cart id=%s", cart_item_id, cart_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item with id={cart_item_id} not found",
            )
        return cart_item

    def _list_items(self, cart_items: list[CartItem]) -> list[Item]:
        """Return item rows matching the provided cart items."""
        item_ids = tuple({cart_item.item_id for cart_item in cart_items})
        if not item_ids:
            logger.trace("No item ids provided for cart list")
            return []
        placeholders = ", ".join("?" for _ in item_ids)
        rows = self._conn.execute(
            f"SELECT * FROM items WHERE id IN ({placeholders})",
            item_ids,
        ).fetchall()
        return [Item.from_row(row) for row in rows]

    def _calculate_line(self, item: Item, quantity: Decimal) -> dict:
        """Return line totals for a cart item including discounts and tax."""
        logger.trace("Calculating cart line for item id=%s", item.id)
        unit_price = item.unit_price
        line_subtotal = self._money(unit_price * quantity)
        discount = self._money(line_subtotal * (item.discount_rate / Decimal("100")))
        taxable = line_subtotal - discount
        tax = self._money(taxable * (item.tax_rate / Decimal("100")))
        line_total = self._money(taxable + tax)
        return {
            "line_subtotal": line_subtotal,
            "line_discount": discount,
            "line_tax": tax,
            "line_total": line_total,
        }

    def _money(self, value: Decimal) -> Decimal:
        """Quantize currency values to two decimal places."""
        logger.trace("Quantizing cart monetary value")
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _empty_totals(self) -> dict:
        """Return a totals payload with zeroed values."""
        logger.trace("Returning empty cart totals")
        zero = Decimal("0.00")
        return {
            "subtotal": zero,
            "discount_total": zero,
            "tax_total": zero,
            "total": zero,
        }

    def update_cart(self, cart_id: int, data: CartUpdate, updated_by: User) -> Cart:
        """Update cart metadata such as the desk number."""
        logger.info("Updating cart id=%s", cart_id)
        cart = self.get_cart(cart_id)
        self._ensure_cart_editable(cart)

        # Check for duplicate desk_number if one is being assigned
        if data.desk_number is not None:
            existing = self._cart_repo.get_by_desk_number(data.desk_number)
            if existing and existing.id != cart.id:
                logger.warning("Desk number %s already assigned to cart id=%s", data.desk_number, existing.id)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Desk number '{data.desk_number}' is already assigned to another cart",
                )

        updated = self._cart_repo.update_desk_number(cart.id, data.desk_number, updated_by.id)
        if not updated:
            logger.warning("Cart id=%s not found for update", cart_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart with id={cart_id} not found",
            )
        logger.info("Cart id=%s updated", cart_id)
        return updated

    def list_carts_with_desk_number(self) -> list[Cart]:
        """Return carts that have a desk number assigned."""
        logger.info("Listing carts with desk_number")
        return self._cart_repo.list_with_desk_number()
