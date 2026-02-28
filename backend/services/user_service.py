"""
User management service: registration, retrieval, update, and soft deletion.

Business rules enforced here:
- Admins can create users of any role.
- Market Owners can only create Employees.
- Soft delete: rows are never physically removed; is_deleted=1 is set instead.
"""
import sqlite3
from typing import Optional
import logging

from fastapi import HTTPException, status

from backend.core.security import hash_password
from backend.models.user import User, UserRole
from backend.repositories.user_repository import UserRepository
from backend.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing UserService")
        self._repo = UserRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_user(self, user_id: int) -> User:
        """Return a non-deleted user or raise 404."""
        logger.info("Fetching user id=%s", user_id)
        user = self._repo.get_active_by_id(user_id)
        if not user:
            logger.warning("User id=%s not found", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )
        return user

    def list_users(self, include_deleted: bool = False) -> list[User]:
        logger.info("Listing users include_deleted=%s", include_deleted)
        return self._repo.list_all(include_deleted=include_deleted)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def register_user(self, data: UserCreate, created_by: User) -> User:
        """
        Create a new user account.

        Rules:
        - **Admin** – may create any role (admin, market_owner, employee).
        - **Market Owner** – may only create Employees.
        """
        logger.info("Registering user %s", data.username)
        # Role-based creation restrictions
        if created_by.role == UserRole.MARKET_OWNER:
            if data.role != UserRole.EMPLOYEE:
                logger.warning(
                    "Market owner id=%s attempted to create role=%s",
                    created_by.id,
                    data.role.value,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Market owners can only create employee accounts",
                )

        # Uniqueness checks (only among non-deleted users)
        if self._repo.get_by_email(data.email):
            logger.warning("Duplicate email registration attempt: %s", data.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )
        if self._repo.get_by_username(data.username):
            logger.warning("Duplicate username registration attempt: %s", data.username)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already taken",
            )

        user = self._repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            role=data.role,
            full_name=data.full_name,
        )
        logger.info("User registered id=%s", user.id)
        return user

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_user(self, user_id: int, data: UserUpdate, updated_by: User) -> User:
        logger.info("Updating user id=%s", user_id)
        target = self.get_user(user_id)  # raises 404 if not found / deleted

        # Market owners can only update employees (users with role='employee')
        if updated_by.role == UserRole.MARKET_OWNER:
            if target.role != UserRole.EMPLOYEE:
                logger.warning(
                    "Market owner id=%s attempted to update non-employee id=%s",
                    updated_by.id,
                    user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update employee accounts",
                )
            # Market owners cannot change roles
            if data.role is not None:
                logger.warning(
                    "Market owner id=%s attempted to change roles for user id=%s",
                    updated_by.id,
                    user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Market owners cannot change user roles",
                )

        updates: dict = {}

        if data.email is not None:
            existing = self._repo.get_by_email(data.email)
            if existing and existing.id != user_id:
                logger.warning("Duplicate email update attempt: %s", data.email)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is already registered",
                )
            updates["email"] = data.email

        if data.full_name is not None:
            updates["full_name"] = data.full_name

        if data.password is not None:
            updates["hashed_password"] = hash_password(data.password)

        if data.role is not None:
            updates["role"] = data.role.value

        if data.is_active is not None:
            updates["is_active"] = int(data.is_active)

        updated_user = self._repo.update(user_id, **updates)  # type: ignore[return-value]
        logger.info("User updated id=%s", user_id)
        return updated_user

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    def delete_user(self, user_id: int, deleted_by: User) -> None:
        """
        Soft-delete a user (sets is_deleted=1, is_active=0, records deleted_at).
        The row is never physically removed from the database.

        Rules:
        - Admins can soft-delete any non-deleted user.
        - Market owners can only soft-delete employees (role='employee').
        - A user can soft-delete their own account.
        """
        logger.info("Deleting user id=%s", user_id)
        target = self.get_user(user_id)  # raises 404 if already deleted

        is_self = deleted_by.id == user_id
        is_admin = deleted_by.role == UserRole.ADMIN
        is_owner_deleting_employee = (
            deleted_by.role == UserRole.MARKET_OWNER
            and target.role == UserRole.EMPLOYEE
        )

        if not (is_self or is_admin or is_owner_deleting_employee):
            logger.warning(
                "User id=%s forbidden from deleting user id=%s",
                deleted_by.id,
                user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this account",
            )

        if not self._repo.soft_delete(user_id):
            logger.warning("User id=%s not found for deletion", user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )
        logger.info("User deleted id=%s", user_id)
