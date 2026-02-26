"""
Category management endpoints (any authenticated user can access):
  POST   /categories           – Create a new category
  GET    /categories           – List all categories
  GET    /categories/{id}      – Get a specific category
  PATCH  /categories/{id}      – Update a category
  DELETE /categories/{id}      – Delete a category
"""
from fastapi import APIRouter, Depends, status

from backend.core.dependencies import db_dependency, get_current_active_user
from backend.models.user import User
from backend.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from backend.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
def create_category(
    data: CategoryCreate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new item category. Any authenticated user can create categories.
    Category names must be unique.
    """
    service = CategoryService(conn)
    return service.create_category(data, created_by=current_user)


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List all categories",
)
def list_categories(
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Return a list of all categories, sorted by name."""
    service = CategoryService(conn)
    return service.list_categories()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a specific category",
)
def get_category(
    category_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """Retrieve a category by its ID."""
    service = CategoryService(conn)
    return service.get_category(category_id)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    conn=Depends(db_dependency),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a category's name or description.
    Any authenticated user can update categories.
    """
    service = CategoryService(conn)
    return service.update_category(category_id, data, updated_by=current_user)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
)
def delete_category(
    category_id: int,
    conn=Depends(db_dependency),
    _: User = Depends(get_current_active_user),
):
    """
    Delete a category. Any authenticated user can delete categories.
    Cannot delete a category that has items assigned to it.
    """
    service = CategoryService(conn)
    service.delete_category(category_id)