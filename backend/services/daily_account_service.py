"""
Daily account management service.
Handles closing daily accounts and retrieving summaries.
"""
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import logging

from fastapi import HTTPException, status

from backend.models.cart import Cart
from backend.models.daily_account import DailyAccount
from backend.models.user import User
from backend.repositories.cart_repository import CartRepository
from backend.repositories.daily_account_repository import DailyAccountRepository
from backend.repositories.item_repository import ItemRepository

logger = logging.getLogger(__name__)


class DailyAccountService:
    """Business logic for daily account close/open workflows."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize repositories used by the daily account service."""
        logger.trace("Initializing DailyAccountService")
        self._conn = conn
        self._account_repo = DailyAccountRepository(conn)
        self._cart_repo = CartRepository(conn)
        self._item_repo = ItemRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_account(self, account_id: int) -> DailyAccount:
        """Fetch a daily account by id or raise a 404 HTTP exception."""
        logger.info("Fetching daily account id=%s", account_id)
        account = self._account_repo.get_by_id(account_id)
        if not account:
            logger.warning("Daily account id=%s not found", account_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Daily account with id={account_id} not found",
            )
        return account

    def get_account_by_date(self, account_date: date) -> DailyAccount:
        """Fetch a daily account by date or raise a 404 HTTP exception."""
        logger.info("Fetching daily account by date=%s", account_date)
        account = self._account_repo.get_by_date(account_date)
        if not account:
            logger.warning("Daily account for date=%s not found", account_date)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Daily account for date={account_date} not found",
            )
        return account

    def get_summary(self, account_id: int) -> dict:
        """Return a daily account summary with items and totals."""
        logger.info("Building daily account summary id=%s", account_id)
        account = self.get_account(account_id)
        items = self._account_repo.list_items_by_account(account.id)
        totals = {
            "subtotal": account.subtotal,
            "discount_total": account.discount_total,
            "tax_total": account.tax_total,
            "total": account.total,
        }
        return {
            "account": account,
            "items": items,
            "totals": totals,
        }

    def list_accounts(self, limit: int = 30) -> list[DailyAccount]:
        """Return recent daily accounts limited by the provided count."""
        logger.info("Listing daily accounts limit=%s", limit)
        return self._account_repo.list_all(limit=limit)

    def list_accounts_by_range(
        self, start_date: date, end_date: date
    ) -> list[DailyAccount]:
        """Return daily accounts within the provided date range."""
        logger.info("Listing daily accounts from %s to %s", start_date, end_date)
        return self._account_repo.list_by_date_range(start_date, end_date)

    # ------------------------------------------------------------------
    # Close account
    # ------------------------------------------------------------------

    def close_today(self, user: User) -> DailyAccount:
        """Close today's account and persist aggregated totals."""
        logger.info("Closing daily account for today user_id=%s", user.id)
        today = date.today()
        existing = self._account_repo.get_by_date(today)

        if existing and existing.is_closed:
            logger.warning("Daily account already closed for date=%s", today)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account for {today} is already closed.",
            )

        # Get today's carts
        carts = self._get_todays_carts()
        if not carts:
            logger.warning("No carts found for daily close date=%s", today)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No carts found for today. Cannot close an empty day.",
            )

        # Aggregate all cart items
        aggregated_items = self._aggregate_cart_items(carts)

        # Calculate totals
        totals = self._calculate_totals(aggregated_items)

        # Create or update the account
        if existing:
            account = self._account_repo.update_totals(
                account_id=existing.id,
                subtotal=float(totals["subtotal"]),
                discount_total=float(totals["discount_total"]),
                tax_total=float(totals["tax_total"]),
                total=float(totals["total"]),
                carts_count=len(carts),
                items_count=len(aggregated_items),
                updated_by=user.id,
            )
            # Clear old items and re-create
            self._account_repo.delete_items_by_account(existing.id)
        else:
            account = self._account_repo.create(
                account_date=today,
                subtotal=float(totals["subtotal"]),
                discount_total=float(totals["discount_total"]),
                tax_total=float(totals["tax_total"]),
                total=float(totals["total"]),
                carts_count=len(carts),
                items_count=len(aggregated_items),
                created_by=user.id,
            )

        # Store aggregated items
        for item_data in aggregated_items:
            self._account_repo.create_item(
                account_id=account.id,
                item_id=item_data["item_id"],
                item_name=item_data["name"],
                sku=item_data["sku"],
                quantity=float(item_data["quantity"]),
                unit_price=float(item_data["unit_price"]),
                discount_rate=float(item_data["discount_rate"]),
                tax_rate=float(item_data["tax_rate"]),
                line_subtotal=float(item_data["line_subtotal"]),
                line_discount=float(item_data["line_discount"]),
                line_tax=float(item_data["line_tax"]),
                line_total=float(item_data["line_total"]),
            )

        # Close the account
        closed_account = self._account_repo.close_account(account.id, closed_by=user.id)
        logger.info("Daily account closed id=%s", account.id)
        return closed_account  # type: ignore[return-value]

    def open_account(self, account_id: int, user: User) -> DailyAccount:
        """Reopen a closed daily account."""
        logger.info("Opening daily account id=%s", account_id)
        account = self.get_account(account_id)

        if not account.is_closed:
            logger.warning("Daily account id=%s already open", account_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account for {account.account_date} is already open.",
            )

        opened_account = self._account_repo.open_account(account.id, opened_by=user.id)
        logger.info("Daily account reopened id=%s", account.id)
        return opened_account  # type: ignore[return-value]

    def close_by_date(self, account_date: date, user: User) -> DailyAccount:
        """Close a specific date's daily account."""
        logger.info("Closing daily account date=%s", account_date)
        existing = self._account_repo.get_by_date(account_date)

        if existing and existing.is_closed:
            logger.warning("Daily account already closed for date=%s", account_date)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account for {account_date} is already closed.",
            )

        # Get carts for the specific date
        carts = self._get_carts_by_date(account_date)
        if not carts:
            logger.warning("No carts found for date=%s", account_date)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No carts found for {account_date}. Cannot close an empty day.",
            )

        # Aggregate all cart items
        aggregated_items = self._aggregate_cart_items(carts)

        # Calculate totals
        totals = self._calculate_totals(aggregated_items)

        # Create or update the account
        if existing:
            account = self._account_repo.update_totals(
                account_id=existing.id,
                subtotal=float(totals["subtotal"]),
                discount_total=float(totals["discount_total"]),
                tax_total=float(totals["tax_total"]),
                total=float(totals["total"]),
                carts_count=len(carts),
                items_count=len(aggregated_items),
                updated_by=user.id,
            )
            self._account_repo.delete_items_by_account(existing.id)
        else:
            account = self._account_repo.create(
                account_date=account_date,
                subtotal=float(totals["subtotal"]),
                discount_total=float(totals["discount_total"]),
                tax_total=float(totals["tax_total"]),
                total=float(totals["total"]),
                carts_count=len(carts),
                items_count=len(aggregated_items),
                created_by=user.id,
            )

        # Store aggregated items
        for item_data in aggregated_items:
            self._account_repo.create_item(
                account_id=account.id,
                item_id=item_data["item_id"],
                item_name=item_data["name"],
                sku=item_data["sku"],
                quantity=float(item_data["quantity"]),
                unit_price=float(item_data["unit_price"]),
                discount_rate=float(item_data["discount_rate"]),
                tax_rate=float(item_data["tax_rate"]),
                line_subtotal=float(item_data["line_subtotal"]),
                line_discount=float(item_data["line_discount"]),
                line_tax=float(item_data["line_tax"]),
                line_total=float(item_data["line_total"]),
            )

        closed_account = self._account_repo.close_account(account.id, closed_by=user.id)
        logger.info("Daily account closed id=%s", account.id)
        return closed_account  # type: ignore[return-value]

    def open_by_date(self, account_date: date, user: User) -> DailyAccount:
        """Reopen a specific date's daily account."""
        logger.info("Opening daily account date=%s", account_date)
        account = self._account_repo.get_by_date(account_date)
        if not account:
            logger.warning("Daily account for date=%s not found", account_date)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Daily account for date={account_date} not found",
            )

        if not account.is_closed:
            logger.warning("Daily account already open for date=%s", account_date)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account for {account_date} is already open.",
            )

        opened_account = self._account_repo.open_account(account.id, opened_by=user.id)
        logger.info("Daily account reopened date=%s", account_date)
        return opened_account  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Data Analysis
    # ------------------------------------------------------------------

    def get_item_sales_by_date_range(
        self, item_id: int, start_date: date, end_date: date
    ) -> dict:
        """Return item sales stats for the provided date range."""
        logger.info("Getting item sales item_id=%s", item_id)
        return self._account_repo.get_item_sales_by_date_range(
            item_id=item_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

    def get_top_sellers(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> list[dict]:
        """Return top selling items for the provided date range."""
        logger.info("Getting top sellers from %s to %s", start_date, end_date)
        return self._account_repo.get_top_sellers(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=limit,
        )

    def get_sales_by_category(
        self, start_date: date, end_date: date
    ) -> list[dict]:
        """Return category sales aggregates for the provided date range."""
        logger.info("Getting sales by category from %s to %s", start_date, end_date)
        return self._account_repo.get_sales_by_category(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_todays_carts(self) -> list[Cart]:
        """Return carts created during the current UTC day."""
        today_start = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        today_end = datetime.now(tz=timezone.utc).replace(
            hour=23, minute=59, second=59, microsecond=999999
        ).isoformat()

        rows = self._conn.execute(
            """
            SELECT * FROM carts
             WHERE created_at >= ? AND created_at <= ?
             ORDER BY id
            """,
            (today_start, today_end),
        ).fetchall()
        logger.trace("Found %s carts for today", len(rows))
        return [Cart.from_row(row) for row in rows]

    def _get_carts_by_date(self, target_date: date) -> list[Cart]:
        """Get carts created on a specific date."""
        date_start = datetime.combine(target_date, datetime.min.time()).replace(
            tzinfo=timezone.utc
        ).isoformat()
        date_end = datetime.combine(target_date, datetime.max.time()).replace(
            tzinfo=timezone.utc
        ).isoformat()

        rows = self._conn.execute(
            """
            SELECT * FROM carts
             WHERE created_at >= ? AND created_at <= ?
             ORDER BY id
            """,
            (date_start, date_end),
        ).fetchall()
        logger.trace("Found %s carts for date=%s", len(rows), target_date)
        return [Cart.from_row(row) for row in rows]

    def _aggregate_cart_items(self, carts: list[Cart]) -> list[dict]:
        """Aggregate items across all carts, summing quantities for same items."""
        cart_ids = tuple(cart.id for cart in carts)
        if not cart_ids:
            logger.trace("No carts provided for aggregation")
            return []

        placeholders = ", ".join("?" for _ in cart_ids)
        rows = self._conn.execute(
            f"""
            SELECT ci.item_id, ci.quantity, i.name, i.sku, i.unit_price,
                   i.discount_rate, i.tax_rate
              FROM cart_items ci
              JOIN items i ON i.id = ci.item_id
             WHERE ci.cart_id IN ({placeholders})
            """,
            cart_ids,
        ).fetchall()

        # Aggregate by item_id
        aggregated: dict[int, dict] = {}
        for row in rows:
            item_id = row["item_id"]
            quantity = Decimal(str(row["quantity"]))
            unit_price = Decimal(str(row["unit_price"]))
            discount_rate = Decimal(str(row["discount_rate"]))
            tax_rate = Decimal(str(row["tax_rate"]))

            if item_id not in aggregated:
                line_subtotal = self._money(unit_price * quantity)
                line_discount = self._money(line_subtotal * (discount_rate / Decimal("100")))
                taxable = line_subtotal - line_discount
                line_tax = self._money(taxable * (tax_rate / Decimal("100")))
                line_total = self._money(taxable + line_tax)

                aggregated[item_id] = {
                    "item_id": item_id,
                    "name": row["name"],
                    "sku": row["sku"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_rate": discount_rate,
                    "tax_rate": tax_rate,
                    "line_subtotal": line_subtotal,
                    "line_discount": line_discount,
                    "line_tax": line_tax,
                    "line_total": line_total,
                }
            else:
                # Add to existing
                aggregated[item_id]["quantity"] += quantity
                # Recalculate line totals
                q = aggregated[item_id]["quantity"]
                up = aggregated[item_id]["unit_price"]
                dr = aggregated[item_id]["discount_rate"]
                tr = aggregated[item_id]["tax_rate"]

                line_subtotal = self._money(up * q)
                line_discount = self._money(line_subtotal * (dr / Decimal("100")))
                taxable = line_subtotal - line_discount
                line_tax = self._money(taxable * (tr / Decimal("100")))
                line_total = self._money(taxable + line_tax)

                aggregated[item_id]["line_subtotal"] = line_subtotal
                aggregated[item_id]["line_discount"] = line_discount
                aggregated[item_id]["line_tax"] = line_tax
                aggregated[item_id]["line_total"] = line_total

        logger.trace("Aggregated %s items from carts", len(aggregated))
        return list(aggregated.values())

    def _calculate_totals(self, items: list[dict]) -> dict:
        """Calculate aggregated totals for a list of line items."""
        logger.trace("Calculating daily account totals")
        subtotal = sum(item["line_subtotal"] for item in items)
        discount_total = sum(item["line_discount"] for item in items)
        tax_total = sum(item["line_tax"] for item in items)
        total = subtotal - discount_total + tax_total

        return {
            "subtotal": self._money(subtotal),
            "discount_total": self._money(discount_total),
            "tax_total": self._money(tax_total),
            "total": self._money(total),
        }

    def _money(self, value: Decimal) -> Decimal:
        """Quantize decimal values to two decimal places."""
        logger.trace("Quantizing decimal value")
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
