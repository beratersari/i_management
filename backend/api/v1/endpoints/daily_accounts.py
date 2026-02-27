"""
Daily account management endpoints:
  POST   /daily-accounts/close              – Close today's account (any authenticated)
  POST   /daily-accounts/{id}/open          – Reopen a closed account (admin/market_owner)
  POST   /daily-accounts/close-by-date      – Close specific date (admin/market_owner)
  POST   /daily-accounts/open-by-date       – Open specific date (admin/market_owner)
  GET    /daily-accounts                    – List recent daily accounts
  GET    /daily-accounts/{id}               – Get daily account summary
  GET    /daily-accounts/by-date/{date}     – Get daily account by date
  GET    /daily-accounts/analysis/item-sales – Get item sales by date range
  GET    /daily-accounts/analysis/top-sellers – Get top selling items
  GET    /daily-accounts/analysis/by-category – Get sales by category
"""
from datetime import date
from fastapi import APIRouter, Depends, Query, status

from backend.core.dependencies import (
    db_dependency,
    get_current_active_user,
    require_admin_or_owner,
)
from backend.models.user import User
from backend.schemas.daily_account import (
    DailyAccountResponse,
    DailyAccountSummaryResponse,
    ItemSalesResponse,
    TopSellerResponse,
    CategorySalesResponse,
)
from backend.services.daily_account_service import DailyAccountService

router = APIRouter(prefix="/daily-accounts", tags=["Daily Accounts"])


@router.post(
    "/close",
    response_model=DailyAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Close today's daily account",
)
def close_today(
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Close the current day's account.
    Aggregates all carts created today and calculates totals.
    Cannot close if already closed or if no carts exist for today.
    """
    service = DailyAccountService(conn)
    return service.close_today(user=current_user)


@router.get(
    "",
    response_model=list[DailyAccountResponse],
    summary="List recent daily accounts",
)
def list_accounts(
    limit: int = Query(30, ge=1, le=100, description="Number of accounts to return"),
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return a list of recent daily accounts, sorted by date descending."""
    service = DailyAccountService(conn)
    return service.list_accounts(limit=limit)


@router.get(
    "/by-date/{account_date}",
    response_model=DailyAccountSummaryResponse,
    summary="Get daily account by date",
)
def get_account_by_date(
    account_date: date,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return a daily account summary for a specific date."""
    service = DailyAccountService(conn)
    return service.get_summary(
        service.get_account_by_date(account_date).id
    )


@router.get(
    "/{account_id}",
    response_model=DailyAccountSummaryResponse,
    summary="Get daily account summary",
)
def get_account(
    account_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return a daily account with all items and totals."""
    service = DailyAccountService(conn)
    return service.get_summary(account_id)


# -----------------------------------------------------------------------------
# Admin/Market Owner endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/{account_id}/open",
    response_model=DailyAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Reopen a closed daily account",
)
def open_account(
    account_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Reopen a closed daily account (admin or market_owner only).
    """
    service = DailyAccountService(conn)
    return service.open_account(account_id, user=current_user)


@router.post(
    "/close-by-date",
    response_model=DailyAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Close a specific date's account",
)
def close_by_date(
    account_date: date,
    conn=Depends(db_dependency),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Close a specific date's daily account (admin or market_owner only).
    Aggregates all carts created on that date and calculates totals.
    """
    service = DailyAccountService(conn)
    return service.close_by_date(account_date, user=current_user)


@router.post(
    "/open-by-date",
    response_model=DailyAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Open a specific date's account",
)
def open_by_date(
    account_date: date,
    conn=Depends(db_dependency),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Reopen a specific date's daily account (admin or market_owner only).
    """
    service = DailyAccountService(conn)
    return service.open_by_date(account_date, user=current_user)


# -----------------------------------------------------------------------------
# Analysis endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/analysis/item-sales",
    response_model=ItemSalesResponse,
    summary="Get item sales by date range",
)
def get_item_sales(
    item_id: int,
    start_date: date,
    end_date: date,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Get sales statistics for a specific item within a date range.
    Example: How many bananas sold between 2024-01-01 and 2024-01-31
    """
    service = DailyAccountService(conn)
    return service.get_item_sales_by_date_range(item_id, start_date, end_date)


@router.get(
    "/analysis/top-sellers",
    response_model=list[TopSellerResponse],
    summary="Get top selling items",
)
def get_top_sellers(
    start_date: date,
    end_date: date,
    limit: int = Query(10, ge=1, le=100, description="Number of top sellers to return"),
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Get top selling items within a date range.
    """
    service = DailyAccountService(conn)
    return service.get_top_sellers(start_date, end_date, limit)


@router.get(
    "/analysis/by-category",
    response_model=list[CategorySalesResponse],
    summary="Get sales by category",
)
def get_sales_by_category(
    start_date: date,
    end_date: date,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Get sales aggregated by category within a date range.
    """
    service = DailyAccountService(conn)
    return service.get_sales_by_category(start_date, end_date)
