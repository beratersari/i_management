"""
Category management service.
Any authenticated user can create, update, and delete categories.
"""
import sqlite3
from typing import Optional

from fastapi import HTTPException, status

from backend.models.category import Category
from backend.models.user import User
from backend.repositories.category_repository import CategoryRepository
from backend.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._repo = CategoryRepository(conn)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_category(self, category_id: int) -> Category:
        category = self._repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id={category_id} not found",
            )
        return category

    def list_categories(self) -> list[Category]:
        return self._repo.list_all()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_category(self, data: CategoryCreate, created_by: User) -> Category:
        # Check for duplicate name
        existing = self._repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{data.name}' already exists",
            )

        return self._repo.create(
            name=data.name,
            description=data.description,
            created_by=created_by.id,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_category(
        self, category_id: int, data: CategoryUpdate, updated_by: User
    ) -> Category:
        category = self.get_category(category_id)

        # Check for name conflict if renaming
        if data.name is not None and data.name != category.name:
            existing = self._repo.get_by_name(data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{data.name}' already exists",
                )

        return self._repo.update(
            category_id=category_id,
            name=data.name,
            description=data.description,
            updated_by=updated_by.id,
        )  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_category(self, category_id: int) -> None:
        category = self.get_category(category_id)
        
        try:
            if not self._repo.delete(category_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id={category_id} not found",
                )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete category: it has items assigned to it",
            )