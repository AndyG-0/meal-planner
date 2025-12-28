"""Recipe endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.database import get_db
from app.models import Recipe, RecipeTag, User, UserFavorite
from app.schemas import (
    RecipeCreate,
    RecipeResponse,
    RecipeTagCreate,
    RecipeTagResponse,
    RecipeUpdate,
)

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Recipe:
    """Create a new recipe."""
    recipe = Recipe(
        **recipe_data.model_dump(),
        owner_id=current_user.id,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.get("", response_model=list[RecipeResponse])
async def list_recipes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str | None = None,
    tags: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[Recipe]:
    """List recipes accessible to the user."""
    query = select(Recipe).where(
        Recipe.deleted_at.is_(None),
        or_(
            Recipe.owner_id == current_user.id,
            Recipe.is_public,
            Recipe.is_shared,
        ),
    )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Recipe.title.ilike(search_pattern),
                Recipe.description.ilike(search_pattern),
            )
        )

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    recipes = result.scalars().all()
    return list(recipes)


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Recipe:
    """Get a recipe by ID."""
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Check access permissions
    if recipe.owner_id != current_user.id and not recipe.is_public and not recipe.is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this recipe",
        )

    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Recipe:
    """Update a recipe."""
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this recipe",
        )

    # Update recipe fields
    update_data = recipe_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recipe, field, value)

    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete a recipe."""
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this recipe",
        )

    recipe.deleted_at = datetime.utcnow()
    await db.commit()


@router.post(
    "/{recipe_id}/tags",
    response_model=RecipeTagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_tag(
    recipe_id: int,
    tag_data: RecipeTagCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeTag:
    """Add a tag to a recipe."""
    # Check if recipe exists and user has permission
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this recipe",
        )

    # Create tag
    tag = RecipeTag(
        recipe_id=recipe_id,
        **tag_data.model_dump(),
    )
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already exists for this recipe",
        )

    return tag


@router.post("/{recipe_id}/favorite", status_code=status.HTTP_201_CREATED)
async def favorite_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Add a recipe to user's favorites."""
    # Check if recipe exists
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Create favorite
    favorite = UserFavorite(
        user_id=current_user.id,
        recipe_id=recipe_id,
    )
    db.add(favorite)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipe already in favorites",
        )

    return {"message": "Recipe added to favorites"}


@router.delete("/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def unfavorite_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a recipe from user's favorites."""
    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id,
            UserFavorite.recipe_id == recipe_id,
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not in favorites",
        )

    await db.delete(favorite)
    await db.commit()
