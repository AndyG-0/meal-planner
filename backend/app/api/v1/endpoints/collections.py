"""Recipe collections API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import get_current_active_user
from app.database import get_db
from app.models import Recipe, RecipeCollection, RecipeCollectionItem, User
from app.schemas import (
    RecipeCollectionCreate,
    RecipeCollectionItemResponse,
    RecipeCollectionResponse,
    RecipeCollectionUpdate,
    RecipeResponse,
    RecipeTagResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collections", tags=["Recipe Collections"])


async def build_collection_response(
    collection: RecipeCollection, db: AsyncSession
) -> RecipeCollectionResponse:
    """Build a collection response with recipe items."""
    # Load collection items with recipes
    result = await db.execute(
        select(RecipeCollectionItem)
        .where(RecipeCollectionItem.collection_id == collection.id)
        .options(selectinload(RecipeCollectionItem.recipe))
    )
    items = result.scalars().all()

    # Build item responses
    item_responses = []
    for item in items:
        item_responses.append(
            RecipeCollectionItemResponse(
                id=item.id,
                recipe_id=item.recipe_id,
                recipe_title=item.recipe.title if item.recipe else None,
                recipe_category=item.recipe.category if item.recipe else None,
                added_at=item.added_at,
            )
        )

    return RecipeCollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        user_id=collection.user_id,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        items=item_responses,
    )


@router.get("", response_model=list[RecipeCollectionResponse])
async def list_collections(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[RecipeCollectionResponse]:
    """Get all recipe collections for the current user with pagination."""
    result = await db.execute(
        select(RecipeCollection)
        .where(
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(limit)
    )
    collections = result.scalars().all()

    # Build responses with items
    responses = []
    for collection in collections:
        response = await build_collection_response(collection, db)
        responses.append(response)

    return responses


@router.post("", response_model=RecipeCollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: RecipeCollectionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeCollectionResponse:
    """Create a new recipe collection."""
    collection = RecipeCollection(
        name=collection_data.name,
        description=collection_data.description,
        user_id=current_user.id,
    )
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return await build_collection_response(collection, db)


@router.get("/{collection_id}", response_model=RecipeCollectionResponse)
async def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeCollectionResponse:
    """Get a specific recipe collection."""
    result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    return await build_collection_response(collection, db)


@router.patch("/{collection_id}", response_model=RecipeCollectionResponse)
async def update_collection(
    collection_id: int,
    collection_data: RecipeCollectionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeCollectionResponse:
    """Update a recipe collection."""
    result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    update_data = collection_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    await db.commit()
    await db.refresh(collection)
    return await build_collection_response(collection, db)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a recipe collection."""
    result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    await db.delete(collection)
    await db.commit()


@router.get("/{collection_id}/recipes", response_model=list[RecipeResponse])
async def get_collection_recipes(
    collection_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[RecipeResponse]:
    """Get all recipes in a collection with full details."""
    # Verify collection exists and belongs to user
    result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Get all recipe IDs in the collection
    items_result = await db.execute(
        select(RecipeCollectionItem.recipe_id)
        .where(RecipeCollectionItem.collection_id == collection_id)
        .offset(skip)
        .limit(limit)
    )
    recipe_ids = [row[0] for row in items_result.all()]

    if not recipe_ids:
        return []

    # Get full recipe details
    from app.models import UserFavorite

    recipes_result = await db.execute(
        select(Recipe)
        .where(Recipe.id.in_(recipe_ids), Recipe.deleted_at.is_(None))
        .options(selectinload(Recipe.tags))
    )
    recipes = recipes_result.scalars().all()

    # Build recipe responses
    recipe_responses = []
    for recipe in recipes:
        # Check if favorited
        favorite_result = await db.execute(
            select(UserFavorite).where(
                UserFavorite.user_id == current_user.id, UserFavorite.recipe_id == recipe.id
            )
        )
        is_favorited = favorite_result.scalar_one_or_none() is not None

        recipe_response = RecipeResponse(
            id=recipe.id,
            owner_id=recipe.owner_id,
            title=recipe.title,
            description=recipe.description,
            ingredients=recipe.ingredients,
            instructions=recipe.instructions,
            serving_size=recipe.serving_size,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            difficulty=recipe.difficulty,
            category=recipe.category,
            nutritional_info=recipe.nutritional_info,
            visibility=recipe.visibility,
            group_id=recipe.group_id,
            is_shared=recipe.is_shared,
            is_public=recipe.is_public,
            image_url=recipe.image_url,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
            is_favorite=is_favorited,
            tags=[RecipeTagResponse.model_validate(tag) for tag in recipe.tags]
            if recipe.tags
            else [],
        )
        recipe_responses.append(recipe_response)

    return recipe_responses


@router.post("/{collection_id}/recipes/{recipe_id}", status_code=status.HTTP_201_CREATED)
async def add_recipe_to_collection(
    collection_id: int,
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a recipe to a collection."""
    # Verify collection exists and belongs to user
    result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Verify recipe exists
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Check if already in collection
    result = await db.execute(
        select(RecipeCollectionItem).where(
            RecipeCollectionItem.collection_id == collection_id,
            RecipeCollectionItem.recipe_id == recipe_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipe already in collection",
        )

    item = RecipeCollectionItem(
        collection_id=collection_id,
        recipe_id=recipe_id,
    )
    db.add(item)
    await db.commit()
    return {"message": "Recipe added to collection"}


@router.delete("/{collection_id}/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recipe_from_collection(
    collection_id: int,
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a recipe from a collection."""
    # Verify collection exists and belongs to user
    result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
            RecipeCollection.deleted_at.is_(None),
        )
    )
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    # Find and delete the item
    result = await db.execute(
        select(RecipeCollectionItem).where(
            RecipeCollectionItem.collection_id == collection_id,
            RecipeCollectionItem.recipe_id == recipe_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not in collection",
        )

    await db.delete(item)
    await db.commit()
