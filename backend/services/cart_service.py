"""
Cart management service.
Store employees can create carts, add/update items, clear carts, and view totals.
"""
import sqlite3
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status

from backend.models.cart import Cart
from backend.models.cart_item import CartItem
from backend.models.item import Item
from backend.models.stock import StockEntry
from backend.models.user import User
from backend.repositories.cart_item_repository import CartItemRepository
from backend.repositories.cart_repository import CartRepository
from backend.repositories.item_repository import ItemRepository
from backend.repositories.stock_repository import StockRepository
from backend.schemas.cart import CartItemCreate, CartItemUpdate


class CartService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._cart_repo = CartRepository(conn)
        self._cart_item_repo = CartItemRepository(conn)
        self._item_repo = ItemRepository(conn)
        self._stock_repo = StockRepository(conn)

    # ------------------------------------------------------------------
    # Cart lifecycle
    # ------------------------------------------------------------------

    def create_cart(self, created_by: User) -> Cart:
        return self._cart_repo.create(created_by=created_by.id)

    def get_cart(self, cart_id: int) -> Cart:
        cart = self._cart_repo.get_by_id(cart_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart with id={cart_id} not found",
            )
        return cart

    # ------------------------------------------------------------------
    # Cart item management
    # ------------------------------------------------------------------

    def add_item(self, cart_id: int, data: CartItemCreate, user: User) -> CartItem:
        """
        Add an item to a cart.
        Raises 409 Conflict if the item already exists in the cart.
        Use PATCH to update quantity of existing items.
        """
        cart = self.get_cart(cart_id)
        item = self._get_item(data.item_id)
        stock = self._get_stock(item.id)

        existing = self._cart_item_repo.get_by_cart_item(cart.id, item.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Item id={item.id} already exists in cart. "
                    f"Use PATCH /carts/{cart.id}/items/{existing.id} to update quantity."
                ),
            )

        self._ensure_stock_available(stock, data.quantity)

        created = self._cart_item_repo.create(
            cart_id=cart.id,
            item_id=item.id,
            quantity=float(data.quantity),
            created_by=user.id,
        )
        self._touch_cart(cart.id, user)
        return created

    def update_item(
        self, cart_id: int, cart_item_id: int, data: CartItemUpdate, user: User
    ) -> CartItem | None:
        """
        Update a cart item's quantity.
        Returns the updated CartItem, or None if the item was deleted (quantity = 0).
        """
        cart = self.get_cart(cart_id)
        cart_item = self._get_cart_item(cart.id, cart_item_id)

        if data.quantity == 0:
            self._cart_item_repo.delete(cart_item.id)
            self._touch_cart(cart.id, user)
            return None

        stock = self._get_stock(cart_item.item_id)
        self._ensure_stock_available(stock, data.quantity)

        updated = self._cart_item_repo.update_quantity(
            cart_item.id, float(data.quantity), updated_by=user.id
        )
        self._touch_cart(cart.id, user)
        return updated  # type: ignore[return-value]

    def clear_cart(self, cart_id: int, user: User) -> int:
        cart = self.get_cart(cart_id)
        cleared = self._cart_item_repo.clear_cart(cart.id)
        self._touch_cart(cart.id, user)
        return cleared

    def list_cart_items(self, cart_id: int) -> list[CartItem]:
        cart = self.get_cart(cart_id)
        return self._cart_item_repo.list_by_cart(cart.id)

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------

    def calculate_totals(self, cart_id: int) -> dict:
        cart = self.get_cart(cart_id)
        cart_items = self._cart_item_repo.list_by_cart(cart.id)
        if not cart_items:
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
                continue

            line = self._calculate_line(item, cart_item.quantity)
            line_items.append({
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
        return {
            "cart": cart,
            "items": line_items,
            "totals": totals,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_item(self, item_id: int) -> Item:
        item = self._item_repo.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id={item_id} not found",
            )
        return item

    def _get_stock(self, item_id: int) -> StockEntry:
        stock = self._stock_repo.get_by_item_id(item_id)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Item id={item_id} is not in stock. "
                    "Add it to stock before adding to a cart."
                ),
            )
        return stock

    def _ensure_stock_available(self, stock: StockEntry, desired_quantity: Decimal) -> None:
        if desired_quantity > stock.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Requested quantity exceeds available stock "
                    f"({desired_quantity} > {stock.quantity})."
                ),
            )

    def _get_cart_item(self, cart_id: int, cart_item_id: int) -> CartItem:
        cart_item = self._cart_item_repo.get_by_id(cart_item_id)
        if cart_item and cart_item.cart_id == cart_id:
            return cart_item

        cart_item = self._cart_item_repo.get_by_cart_item(cart_id, cart_item_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cart item with id={cart_item_id} not found",
            )
        return cart_item

    def _list_items(self, cart_items: list[CartItem]) -> list[Item]:
        item_ids = tuple({cart_item.item_id for cart_item in cart_items})
        if not item_ids:
            return []
        placeholders = ", ".join("?" for _ in item_ids)
        rows = self._conn.execute(
            f"SELECT * FROM items WHERE id IN ({placeholders})",
            item_ids,
        ).fetchall()
        return [Item.from_row(row) for row in rows]

    def _calculate_line(self, item: Item, quantity: Decimal) -> dict:
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
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _empty_totals(self) -> dict:
        zero = Decimal("0.00")
        return {
            "subtotal": zero,
            "discount_total": zero,
            "tax_total": zero,
            "total": zero,
        }

    def _touch_cart(self, cart_id: int, user: User) -> None:
        self._cart_repo.touch(cart_id, updated_by=user.id)
