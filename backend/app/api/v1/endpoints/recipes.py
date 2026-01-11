"""Recipe endpoints."""

import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import get_current_active_user
from app.config import settings
from app.database import get_db
from app.models import GroupMember, Recipe, RecipeRating, RecipeTag, User, UserFavorite
from app.schemas import (
    PaginatedRecipeResponse,
    PaginationMetadata,
    RecipeCreate,
    RecipeQuickAdd,
    RecipeRatingCreate,
    RecipeRatingResponse,
    RecipeResponse,
    RecipeTagCreate,
    RecipeTagResponse,
    RecipeUpdate,
)
from app.services.nutrition import calculate_recipe_nutrition
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recipes", tags=["Menu Items"])


def clean_ingredient_data(ingredients: list) -> list:
    """Clean malformed ingredient data from database.

    Fixes ingredients that have measurements in the name field by
    attempting to parse and restructure them correctly.
    """
    if not ingredients:
        return []

    cleaned = []
    for ing in ingredients:
        if not isinstance(ing, dict):
            continue

        name = ing.get("name", "").strip()
        quantity = ing.get("quantity")
        unit = ing.get("unit", "").strip()

        # Skip empty ingredients
        if not name:
            continue

        # Check if name contains measurements and try to fix it
        if name and (name[0].isdigit() or name.startswith("(")):
            # Try to parse "1/2 cup flour" or "(100 g) cheese, softened"
            # Pattern: optional (number unit) or number/number unit, followed by name
            patterns = [
                r"^\(([\d.]+)\s*([a-zA-Z]+)\)\s*(.+)$",  # (100 g) cheese
                r"^([\d./]+)\s+([a-zA-Z]+)\s+(.+)$",  # 1/2 cup flour
            ]

            parsed = False
            for pattern in patterns:
                match = re.match(pattern, name)
                if match:
                    try:
                        parsed_qty = match.group(1)
                        # Handle fractions like 1/2
                        if "/" in parsed_qty:
                            parts = parsed_qty.split("/")
                            parsed_qty = float(parts[0]) / float(parts[1])
                        else:
                            parsed_qty = float(parsed_qty)

                        parsed_unit = match.group(2)
                        parsed_name = match.group(3).strip(", ")

                        # Use parsed values if current values are generic
                        if unit == "serving" or not unit:
                            unit = parsed_unit
                        if quantity == 1 or not quantity:
                            quantity = parsed_qty
                        name = parsed_name
                        parsed = True
                        break
                    except (ValueError, IndexError):
                        continue

            # If we couldn't parse, try to extract just the ingredient name
            if not parsed:
                # Remove leading measurements
                name = re.sub(r"^[\d./\s()]+[a-zA-Z]+\s+", "", name)
                name = name.strip(", ")

        # Ensure we have valid data
        if not name:
            continue
        if not quantity or not isinstance(quantity, (int, float)):
            quantity = 1.0
        if not unit:
            unit = "serving"

        cleaned.append({"name": name, "quantity": float(quantity), "unit": unit})

    return cleaned


@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Create a new recipe."""
    logger.info("Creating recipe: user_id=%s", current_user.id)

    # If no image URL is provided, use the default placeholder image
    recipe_dict = recipe_data.model_dump()
    if not recipe_dict.get("image_url"):
        image_url = settings.DEFAULT_RECIPE_IMAGE
        if image_url and not image_url.startswith(("http://", "https://")):
            image_url = f"{settings.BACKEND_URL}{image_url}"
        recipe_dict["image_url"] = image_url

    recipe = Recipe(
        **recipe_dict,
        owner_id=current_user.id,
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)

    logger.info("Recipe created successfully: recipe_id=%s", recipe.id)
    # Create RecipeResponse with all fields including is_favorite=False
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
        is_favorite=False,  # New recipes are not favorited
        tags=[],  # New recipes have no tags initially
    )

    return recipe_response


@router.post("/quick-add", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def quick_add_menu_item(
    quick_data: RecipeQuickAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Quick-add a menu item with minimal information (title only required).

    This endpoint allows users to quickly add menu items to their calendar
    without requiring full recipe details. The menu item is created as private
    by default and can be edited later to add more details.
    """
    logger.info("Quick-adding menu item: user_id=%s, title=%s", current_user.id, quick_data.title)

    # Try to find an image for the menu item
    image_url = None
    try:
        # Initialize OpenAI service to use image search
        openai_service = OpenAIService(db)
        await openai_service.initialize()

        # Search for an image based on the title
        logger.info(f"Searching for image for menu item: {quick_data.title}")
        image_results = await openai_service.search_images(quick_data.title, max_results=1)

        if image_results and len(image_results) > 0:
            image_url = image_results[0].get("url")
            logger.info(f"Found image for menu item: {image_url}")
        else:
            logger.info("No images found, using default")
            image_url = settings.DEFAULT_RECIPE_IMAGE
            if image_url and not image_url.startswith(("http://", "https://")):
                image_url = f"{settings.BACKEND_URL}{image_url}"
    except Exception as e:
        logger.warning(f"Image search failed: {str(e)}, using default")
        image_url = settings.DEFAULT_RECIPE_IMAGE
        if image_url and not image_url.startswith(("http://", "https://")):
            image_url = f"{settings.BACKEND_URL}{image_url}"

    # Create recipe with minimal data - ingredients and instructions are optional
    recipe = Recipe(
        title=quick_data.title,
        category=quick_data.category,
        owner_id=current_user.id,
        visibility="private",  # Always private for quick-add
        ingredients=None,  # Optional
        instructions=None,  # Optional
        image_url=image_url,  # Add the found or default image
    )
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)

    logger.info("Menu item quick-added successfully: recipe_id=%s", recipe.id)

    # Create RecipeResponse
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
        is_favorite=False,
        tags=[],
    )

    return recipe_response


@router.get("", response_model=PaginatedRecipeResponse)
async def list_recipes(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    search: str | None = None,
    tags: str | None = Query(None, description="Comma-separated list of tags to filter by"),
    category: str | None = Query(None, description="Recipe category filter"),
    difficulty: str | None = Query(None, description="Recipe difficulty filter"),
    dietary: str | None = Query(
        None, description="Dietary preference filter (tag) - deprecated, use tags"
    ),
    max_prep_time: int | None = Query(None, description="Maximum prep time in minutes"),
    max_cook_time: int | None = Query(None, description="Maximum cook time in minutes"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedRecipeResponse:
    """List recipes accessible to the user with optional filters and pagination."""
    logger.debug(
        "Listing recipes: user_id=%s, page=%d, page_size=%d, category=%s",
        current_user.id, page, page_size, category
    )
    # Get user's group IDs
    group_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
    )
    user_group_ids = [row[0] for row in group_result.all()]

    # Build query for accessible recipes
    query = (
        select(Recipe)
        .where(
            Recipe.deleted_at.is_(None),
            or_(
                Recipe.owner_id == current_user.id,  # User's own recipes
                Recipe.visibility == "public",  # Public recipes
                (Recipe.visibility == "group")
                & (Recipe.group_id.in_(user_group_ids)),  # Group recipes
            ),
        )
        .options(selectinload(Recipe.tags))
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

    # Apply category filter
    if category:
        query = query.where(Recipe.category == category)

    # Apply difficulty filter
    if difficulty:
        query = query.where(Recipe.difficulty == difficulty)

    # Apply prep time filter
    if max_prep_time is not None:
        query = query.where(or_(Recipe.prep_time.is_(None), Recipe.prep_time <= max_prep_time))

    # Apply cook time filter
    if max_cook_time is not None:
        query = query.where(or_(Recipe.cook_time.is_(None), Recipe.cook_time <= max_cook_time))

    # Apply tags filter (supports multiple comma-separated tags)
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            query = query.join(RecipeTag).where(RecipeTag.tag_name.in_(tag_list)).distinct()

    # Apply dietary preference filter (backward compatibility)
    elif dietary:
        query = query.join(RecipeTag).where(RecipeTag.tag_name.ilike(f"%{dietary}%")).distinct()

    # Get total count before applying pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    skip = (page - 1) * page_size
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    recipes = result.scalars().all()

    # Get user's favorited recipe IDs
    favorites_result = await db.execute(
        select(UserFavorite.recipe_id).where(UserFavorite.user_id == current_user.id)
    )
    favorited_recipe_ids = {row[0] for row in favorites_result.all()}

    # Convert to response format with is_favorite field
    response_recipes = []
    for recipe in recipes:
        if recipe.ingredients:
            recipe.ingredients = clean_ingredient_data(recipe.ingredients)

        # Load tags eagerly to avoid lazy loading issues
        tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
        recipe_tags = tag_result.scalars().all()

        # Create RecipeResponse with all fields including is_favorite and tags
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
            is_favorite=recipe.id in favorited_recipe_ids,
            tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
        )
        response_recipes.append(recipe_response)

    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedRecipeResponse(
        items=response_recipes,
        pagination=PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )


@router.get("/tags/all", response_model=dict)
async def get_all_tags(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get all unique tags used in recipes accessible to the user."""
    # Get user's group IDs
    group_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
    )
    user_group_ids = [row[0] for row in group_result.all()]

    # Get tags from accessible recipes
    result = await db.execute(
        select(RecipeTag.tag_name, RecipeTag.tag_category, func.count(RecipeTag.id).label("count"))
        .join(Recipe, Recipe.id == RecipeTag.recipe_id)
        .where(
            Recipe.deleted_at.is_(None),
            or_(
                Recipe.owner_id == current_user.id,
                Recipe.visibility == "public",
                (Recipe.visibility == "group") & (Recipe.group_id.in_(user_group_ids)),
            ),
        )
        .group_by(RecipeTag.tag_name, RecipeTag.tag_category)
        .order_by(RecipeTag.tag_name)
    )

    tags_data = result.all()

    # Group tags by category
    tags_by_category = {}
    for tag_name, tag_category, count in tags_data:
        category = tag_category or "other"
        if category not in tags_by_category:
            tags_by_category[category] = []
        tags_by_category[category].append({"name": tag_name, "count": count})

    return tags_by_category


@router.get("/favorites", response_model=list[RecipeResponse])
async def list_favorite_recipes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[RecipeResponse]:
    """List user's favorite recipes."""
    result = await db.execute(
        select(Recipe)
        .join(UserFavorite, UserFavorite.recipe_id == Recipe.id)
        .where(
            UserFavorite.user_id == current_user.id,
            Recipe.deleted_at.is_(None),
        )
        .options(selectinload(Recipe.tags))
        .offset(skip)
        .limit(limit)
    )
    recipes = result.scalars().all()

    # Convert to response format with is_favorite set to True
    response_recipes = []
    for recipe in recipes:
        if recipe.ingredients:
            recipe.ingredients = clean_ingredient_data(recipe.ingredients)

        # Load tags eagerly to avoid lazy loading issues
        tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
        recipe_tags = tag_result.scalars().all()

        # Create RecipeResponse with all fields including is_favorite=True
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
            is_favorite=True,  # All recipes in favorites are favorited
            tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
        )
        response_recipes.append(recipe_response)

    return response_recipes


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Get a recipe by ID."""
    result = await db.execute(
        select(Recipe)
        .where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
        .options(selectinload(Recipe.tags))
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Check access permissions
    can_access = (
        recipe.visibility == "public" or recipe.owner_id == current_user.id or current_user.is_admin
    )

    # Check group access
    if not can_access and recipe.visibility == "group" and recipe.group_id:
        group_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == recipe.group_id, GroupMember.user_id == current_user.id
            )
        )
        can_access = group_result.scalar_one_or_none() is not None

    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this recipe",
        )

    # Clean malformed ingredient data
    if recipe.ingredients:
        recipe.ingredients = clean_ingredient_data(recipe.ingredients)

    # Check if recipe is favorited by current user
    favorite_result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id, UserFavorite.recipe_id == recipe_id
        )
    )
    is_favorited = favorite_result.scalar_one_or_none() is not None

    # Load tags eagerly to avoid lazy loading issues
    tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
    recipe_tags = tag_result.scalars().all()

    # Create RecipeResponse with all fields including is_favorite
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
        tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
    )

    return recipe_response


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Update a recipe."""
    logger.info("Updating recipe: recipe_id=%s, user_id=%s", recipe_id, current_user.id)
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        logger.warning("Recipe not found for update: recipe_id=%s", recipe_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    # Check if user can edit
    can_edit = recipe.owner_id == current_user.id or current_user.is_admin

    # Group admins can also edit group recipes
    if not can_edit and recipe.visibility == "group" and recipe.group_id:
        group_result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == recipe.group_id,
                GroupMember.user_id == current_user.id,
                GroupMember.role == "admin",
            )
        )
        can_edit = group_result.scalar_one_or_none() is not None

    if not can_edit:
        logger.warning("Unauthorized recipe update attempt: recipe_id=%s, user_id=%s", recipe_id, current_user.id)
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

    # Check if recipe is favorited by current user
    favorite_result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id, UserFavorite.recipe_id == recipe_id
        )
    )
    is_favorited = favorite_result.scalar_one_or_none() is not None

    # Load tags eagerly to avoid lazy loading issues
    tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
    recipe_tags = tag_result.scalars().all()

    # Create RecipeResponse with all fields including is_favorite
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
        tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
    )

    return recipe_response


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete a recipe."""
    logger.info("Deleting recipe: recipe_id=%s, user_id=%s", recipe_id, current_user.id)
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        logger.warning("Recipe not found for deletion: recipe_id=%s", recipe_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.owner_id != current_user.id and not current_user.is_admin:
        logger.warning("Unauthorized recipe deletion attempt: recipe_id=%s, user_id=%s", recipe_id, current_user.id)
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


@router.delete("/{recipe_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recipe_tag(
    recipe_id: int,
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a tag from a recipe."""
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

    # Get and delete tag
    result = await db.execute(
        select(RecipeTag).where(
            RecipeTag.id == tag_id,
            RecipeTag.recipe_id == recipe_id,
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await db.delete(tag)
    await db.commit()


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


@router.post("/{recipe_id}/image", response_model=RecipeResponse)
async def upload_recipe_image(
    recipe_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Upload an image for a recipe."""
    logger.info("Uploading image for recipe: recipe_id=%s, user_id=%s", recipe_id, current_user.id)
    # Check if recipe exists and user has permission
    result = await db.execute(
        select(Recipe).where(
            Recipe.id == recipe_id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipe = result.scalar_one_or_none()

    if not recipe:
        logger.warning("Recipe not found for image upload: recipe_id=%s", recipe_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    if recipe.owner_id != current_user.id and not current_user.is_admin:
        logger.warning("Unauthorized image upload attempt: recipe_id=%s, user_id=%s", recipe_id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this recipe",
        )

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning("Invalid file type for image upload: %s", file.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/recipes")
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename or "image.jpg").suffix
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / filename

    # Save file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info("Image saved successfully: recipe_id=%s, filename=%s", recipe_id, filename)
    except Exception as e:
        logger.error("Failed to save image for recipe_id=%s: %s", recipe_id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}",
        )

    # Update recipe with image URL (use full backend URL)
    recipe.image_url = f"{settings.BACKEND_URL}/uploads/recipes/{filename}"
    await db.commit()
    await db.refresh(recipe)

    # Load tags eagerly to avoid lazy loading issues
    tag_result = await db.execute(select(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
    recipe_tags = tag_result.scalars().all()

    # Check if favorited
    favorite_result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id, UserFavorite.recipe_id == recipe.id
        )
    )
    is_favorited = favorite_result.scalar_one_or_none() is not None

    # Return properly constructed response
    return RecipeResponse(
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
        tags=[RecipeTagResponse.model_validate(tag) for tag in recipe_tags],
    )


@router.post(
    "/{recipe_id}/ratings",
    response_model=RecipeRatingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def rate_recipe(
    recipe_id: int,
    rating_data: RecipeRatingCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeRating:
    """Rate a recipe."""
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

    # Check if user already rated this recipe
    result = await db.execute(
        select(RecipeRating).where(
            RecipeRating.recipe_id == recipe_id,
            RecipeRating.user_id == current_user.id,
        )
    )
    existing_rating = result.scalar_one_or_none()

    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        existing_rating.review = rating_data.review
        await db.commit()
        await db.refresh(existing_rating)
        return existing_rating
    else:
        # Create new rating
        rating = RecipeRating(
            recipe_id=recipe_id,
            user_id=current_user.id,
            rating=rating_data.rating,
            review=rating_data.review,
        )
        db.add(rating)
        await db.commit()
        await db.refresh(rating)
        return rating


@router.get("/{recipe_id}/ratings", response_model=list[RecipeRatingResponse])
async def get_recipe_ratings(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[RecipeRating]:
    """Get ratings for a recipe."""
    result = await db.execute(
        select(RecipeRating)
        .options(selectinload(RecipeRating.user))
        .where(RecipeRating.recipe_id == recipe_id)
        .offset(skip)
        .limit(limit)
    )
    ratings = result.scalars().all()
    return list(ratings)


@router.delete("/{recipe_id}/ratings", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    recipe_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete user's rating for a recipe."""
    result = await db.execute(
        select(RecipeRating).where(
            RecipeRating.recipe_id == recipe_id,
            RecipeRating.user_id == current_user.id,
        )
    )
    rating = result.scalar_one_or_none()

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found",
        )

    await db.delete(rating)
    await db.commit()


@router.get("/{recipe_id}/nutrition")
async def calculate_nutrition(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Calculate nutrition information for a recipe."""
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    recipe = result.scalar_one_or_none()

    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )

    nutrition = calculate_recipe_nutrition(
        recipe.ingredients or [],
        recipe.serving_size or 4,
    )

    return nutrition


@router.get("/export/all")
async def export_recipes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export all user's recipes as JSON."""
    result = await db.execute(
        select(Recipe).where(
            Recipe.owner_id == current_user.id,
            Recipe.deleted_at.is_(None),
        )
    )
    recipes = result.scalars().all()

    export_data = []
    for recipe in recipes:
        export_data.append(
            {
                "title": recipe.title,
                "description": recipe.description,
                "ingredients": recipe.ingredients,
                "instructions": recipe.instructions,
                "serving_size": recipe.serving_size,
                "prep_time": recipe.prep_time,
                "cook_time": recipe.cook_time,
                "difficulty": recipe.difficulty,
                "category": recipe.category,
                "nutritional_info": recipe.nutritional_info,
            }
        )

    json_content = json.dumps(export_data, indent=2)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f"attachment; filename=recipes_{datetime.now().strftime('%Y%m%d')}.json"
            )
        },
    )


def get_default_image_url() -> None:
    """Return None to use the default preview image for recipes without images.

    The frontend will display the default placeholder when image_url is None.
    """
    return None


async def get_or_create_seed_user(db: AsyncSession) -> User:
    """Get or create the seed user for storing seed recipes.

    Admins can edit these recipes because the permission check includes:
    can_edit = recipe.owner_id == current_user.id or current_user.is_admin
    """
    # Check if seed user exists
    result = await db.execute(select(User).where(User.username == "_seed_recipes"))
    seed_user = result.scalars().first()

    if seed_user:
        return seed_user

    from app.utils.auth import get_password_hash

    seed_user = User(
        username="_seed_recipes",
        email="seed@recipes.local",
        password_hash=get_password_hash("seed_password_123"),
        is_admin=False,
    )
    db.add(seed_user)
    await db.commit()
    await db.refresh(seed_user)
    logger.info("Created seed user for seed recipes")
    return seed_user


@router.post("/seed/import")
async def import_seed_recipes(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Import seed recipes from the default seed file.

    Non-destructive: Only adds recipes that don't already exist with the same title
    for the seed user. Does not modify existing recipes.
    """
    try:
        # Get the seed recipes file from the backend data directory
        seed_file = Path(__file__).parent.parent.parent.parent / "data" / "seed_recipes.json"
        if not seed_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seed recipes file not found on server",
            )

        with open(seed_file, encoding="utf-8") as f:
            seed_data = json.load(f)

        if not isinstance(seed_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid seed file format. Expected a JSON array of recipes.",
            )

        # Seed recipes will have a dedicated _seed_recipes user owner
        # but admins can still edit them due to the permission check:
        # can_edit = recipe.owner_id == current_user.id or current_user.is_admin
        seed_user = await get_or_create_seed_user(db)

        imported_count = 0
        skipped_count = 0
        errors = []

        for idx, recipe_data in enumerate(seed_data):
            try:
                # Check if recipe already exists (by title and seed user)
                result = await db.execute(
                    select(Recipe).where(
                        Recipe.title == recipe_data.get("title"),
                        Recipe.owner_id == seed_user.id,
                    )
                )
                existing = result.scalars().first()

                if existing:
                    skipped_count += 1
                    continue

                # Validate required fields
                if "title" not in recipe_data:
                    errors.append(f"Recipe {idx + 1}: Missing title")
                    continue

                recipe = Recipe(
                    title=recipe_data.get("title"),
                    description=recipe_data.get("description"),
                    owner_id=seed_user.id,  # Owned by seed user, but admins can still edit
                    ingredients=recipe_data.get("ingredients"),
                    instructions=recipe_data.get("instructions"),
                    serving_size=recipe_data.get("serving_size", 4),
                    prep_time=recipe_data.get("prep_time"),
                    cook_time=recipe_data.get("cook_time"),
                    difficulty=recipe_data.get("difficulty"),
                    category=recipe_data.get("category", "staple"),
                    nutritional_info=recipe_data.get("nutritional_info"),
                    visibility="public",
                    image_url=None,  # Use default preview image
                )
                db.add(recipe)
                imported_count += 1

            except Exception as exc:  # noqa: BLE001, F841
                errors.append(f"Recipe {idx + 1}: {str(exc)}")

        await db.commit()

        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors if errors else None,
            "message": f"Successfully imported {imported_count} seed recipes ({skipped_count} already existed)",
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in seed file",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Seed import failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed import failed: {str(e)}",
        )


@router.post("/import")
async def import_recipes(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Import recipes from JSON file."""
    try:
        content = await file.read()
        recipes_data = json.loads(content)

        if not isinstance(recipes_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Expected a JSON array of recipes.",
            )

        imported_count = 0
        errors = []

        for idx, recipe_data in enumerate(recipes_data):
            try:
                # Validate required fields
                if "title" not in recipe_data or "ingredients" not in recipe_data:
                    errors.append(f"Recipe {idx + 1}: Missing required fields")
                    continue

                recipe = Recipe(
                    title=recipe_data.get("title"),
                    description=recipe_data.get("description"),
                    owner_id=current_user.id,
                    ingredients=recipe_data.get("ingredients", []),
                    instructions=recipe_data.get("instructions", []),
                    serving_size=recipe_data.get("serving_size", 4),
                    prep_time=recipe_data.get("prep_time"),
                    cook_time=recipe_data.get("cook_time"),
                    difficulty=recipe_data.get("difficulty"),
                    category=recipe_data.get("category"),
                    nutritional_info=recipe_data.get("nutritional_info"),
                    visibility="private",
                )
                db.add(recipe)
                imported_count += 1

            except Exception as e:
                errors.append(f"Recipe {idx + 1}: {str(e)}")

        await db.commit()

        return {
            "imported": imported_count,
            "errors": errors if errors else None,
            "message": f"Successfully imported {imported_count} recipes",
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file",
        )
    except HTTPException:
        # Re-raise HTTPExceptions (e.g., validation errors) so they are returned as intended
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}",
        )


@router.get("/download-image")
async def download_image_proxy(
    image_url: str = Query(..., description="URL of the image to download"),
) -> Response:
    """Proxy endpoint to download images from external URLs to avoid CORS issues.

    This endpoint fetches an image from an external URL and returns it to the client,
    bypassing CORS restrictions that would prevent direct client-side fetching.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(image_url, follow_redirects=True)
            response.raise_for_status()

            # Get content type from response or default to jpeg
            content_type = response.headers.get("content-type", "image/jpeg")

            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600",
                },
            )
    except httpx.HTTPError as e:
        logger.error("Failed to download image from %s: %s", image_url, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error downloading image: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download image",
        )
