"""
Category management service.
Any authenticated user can create, update, and delete categories.
"""
import sqlite3
from typing import Optional
import logging

from fastapi import HTTPException, status

from backend.models.category import Category
from backend.models.user import User
from backend.repositories.category_repository import CategoryRepository
from backend.schemas.category import CategoryCreate, CategoryUpdate

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        logger.trace("Initializing CategoryService")
        self._repo = CategoryRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_category(self, category_id: int) -> Category:
        logger.info("Fetching category id=%s", category_id)
        category = self._repo.get_by_id(category_id)
        if not category:
            logger.warning("Category id=%s not found", category_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id={category_id} not found",
            )
        return category

    def list_categories(self) -> list[Category]:
        logger.info("Listing categories")
        return self._repo.list_all()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_category(self, data: CategoryCreate, created_by: User) -> Category:
        # Check for duplicate name
        logger.info("Creating category %s", data.name)
        existing = self._repo.get_by_name(data.name)
        if existing:
            logger.warning("Duplicate category name: %s", data.name)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{data.name}' already exists",
            )

        category = self._repo.create(
            name=data.name,
            description=data.description,
            created_by=created_by.id,
        )
        logger.info("Category created id=%s", category.id)
        return category

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_category(
        self, category_id: int, data: CategoryUpdate, updated_by: User
    ) -> Category:
        logger.info("Updating category id=%s", category_id)
        category = self.get_category(category_id)

        # Check for name conflict if renaming
        if data.name is not None and data.name != category.name:
            existing = self._repo.get_by_name(data.name)
            if existing:
                logger.warning("Duplicate category rename attempt: %s", data.name)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{data.name}' already exists",
                )

        updated_category = self._repo.update(
            category_id=category_id,
            name=data.name,
            description=data.description,
            sort_order=data.sort_order,
            updated_by=updated_by.id,
        )  # type: ignore[return-value]
        logger.info("Category updated id=%s", category_id)
        return updated_category

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_category(self, category_id: int) -> None:
        logger.info("Deleting category id=%s", category_id)
        category = self.get_category(category_id)
        logger.trace("Deleting category id=%s name=%s", category_id, category.name)

        try:
            if not self._repo.delete(category_id):
                logger.warning("Category id=%s not found for deletion", category_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id={category_id} not found",
                )
        except sqlite3.IntegrityError:
            logger.warning("Category id=%s delete failed due to assigned items", category_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete category: it has items assigned to it",
            )
        logger.info("Category deleted id=%s", category_id)