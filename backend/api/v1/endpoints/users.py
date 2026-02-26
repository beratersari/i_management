"""
User management endpoints:
  POST   /users/register          – Create a user (Admin or Market Owner)
  GET    /users                   – List all users (Admin only)
  GET    /users/{id}              – Get a specific user (Admin or self)
  PATCH  /users/{id}              – Update a user (Admin or Market Owner for employees)
  DELETE /users/{id}              – Soft-delete a user (Admin, Market Owner, or self)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.core.dependencies import (
    db_dependency,
    get_current_active_user,
    require_admin,
    require_admin_or_owner,
)
from backend.models.user import User, UserRole
from backend.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (Admin or Market Owner)",
)
def register_user(
    data: UserCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Create a new user account.

    - **Admin** – can create any role (`admin`, `market_owner`, `employee`).
    - **Market Owner** – can only create `employee` accounts.

    Password rules: >= 8 characters, at least one uppercase letter and one digit.
    """
    service = UserService(conn)
    return service.register_user(data, created_by=current_user)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users (Admin only)",
)
def list_users(
    include_deleted: bool = Query(False, description="Include soft-deleted users"),
    conn=Depends(db_dependency),
    _: User = Depends(require_admin),
):
    """
    Return a list of every registered user. Restricted to **Admins**.
    Pass `?include_deleted=true` to also see soft-deleted accounts.
    """
    service = UserService(conn)
    return service.list_users(include_deleted=include_deleted)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user (Admin or self)",
)
def get_user(
    user_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve a user by ID.
    - **Admins** can fetch any user.
    - **Market Owners** can fetch any employee (role='employee') or themselves.
    - **Employees** can only fetch their own profile.
    """
    service = UserService(conn)
    target = service.get_user(user_id)

    is_self = current_user.id == user_id
    is_admin = current_user.role == UserRole.ADMIN
    is_owner_viewing_employee = (
        current_user.role == UserRole.MARKET_OWNER
        and target.role == UserRole.EMPLOYEE
    )

    if not (is_self or is_admin or is_owner_viewing_employee):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile",
        )
    return target


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user (Admin or Market Owner for employees)",
)
def update_user(
    user_id: int,
    data: UserUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Update one or more fields of a user account.
    - **Admins** can update any field for any user.
    - **Market Owners** can update employees (role='employee') but cannot change roles.
    """
    service = UserService(conn)
    return service.update_user(user_id, data, updated_by=current_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a user (Admin, Market Owner for employees, or self)",
)
def delete_user(
    user_id: int,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Soft-delete a user account. The row is **never physically removed** from
    the database – `is_deleted` is set to `true` and `deleted_at` is recorded.

    - **Admins** can delete any user.
    - **Market Owners** can delete employees (role='employee').
    - Any user can delete their own account.
    """
    service = UserService(conn)
    service.delete_user(user_id, deleted_by=current_user)
