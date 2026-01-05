"""Admin API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_db
from app.models import (
    Calendar,
    FeatureToggle,
    Group,
    GroupMember,
    OpenAISettings,
    Recipe,
    SessionSettings,
    User,
)
from app.schemas import (
    AdminStatsResponse,
    AdminUserListResponse,
    AdminUserUpdate,
    FeatureToggleCreate,
    FeatureToggleResponse,
    FeatureToggleUpdate,
    OpenAIModelInfo,
    OpenAIModelsListResponse,
    OpenAISettingsResponse,
    OpenAISettingsUpdate,
    RecipeResponse,
    RecipeUpdate,
    SessionSettingsResponse,
    SessionSettingsUpdate,
    UserResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency to require admin privileges."""
    if not bool(current_user.is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> AdminStatsResponse:
    """Get admin dashboard statistics."""

    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    total_recipes_result = await db.execute(
        select(func.count(Recipe.id)).where(Recipe.deleted_at.is_(None))
    )
    total_recipes = total_recipes_result.scalar() or 0

    total_calendars_result = await db.execute(select(func.count(Calendar.id)))
    total_calendars = total_calendars_result.scalar() or 0

    total_groups_result = await db.execute(select(func.count(Group.id)))
    total_groups = total_groups_result.scalar() or 0

    total_public_result = await db.execute(
        select(func.count(Recipe.id)).where(
            Recipe.deleted_at.is_(None), Recipe.visibility == "public"
        )
    )
    total_public_recipes = total_public_result.scalar() or 0

    total_group_result = await db.execute(
        select(func.count(Recipe.id)).where(
            Recipe.deleted_at.is_(None), Recipe.visibility == "group"
        )
    )
    total_group_recipes = total_group_result.scalar() or 0

    total_private_result = await db.execute(
        select(func.count(Recipe.id)).where(
            Recipe.deleted_at.is_(None), Recipe.visibility == "private"
        )
    )
    total_private_recipes = total_private_result.scalar() or 0

    return AdminStatsResponse(
        total_users=total_users,
        total_recipes=total_recipes,
        total_calendars=total_calendars,
        total_groups=total_groups,
        total_public_recipes=total_public_recipes,
        total_group_recipes=total_group_recipes,
        total_private_recipes=total_private_recipes,
    )


@router.get("/users", response_model=list[AdminUserListResponse])
async def list_all_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100,
) -> list[AdminUserListResponse]:
    """List all users with statistics."""

    users_result = await db.execute(
        select(User).where(User.deleted_at.is_(None)).offset(skip).limit(limit)
    )
    users = users_result.scalars().all()

    result = []
    for user in users:
        recipe_count_result = await db.execute(
            select(func.count(Recipe.id)).where(
                Recipe.owner_id == user.id, Recipe.deleted_at.is_(None)
            )
        )
        recipe_count = recipe_count_result.scalar() or 0

        calendar_count_result = await db.execute(
            select(func.count(Calendar.id)).where(Calendar.owner_id == user.id)
        )
        calendar_count = calendar_count_result.scalar() or 0

        group_count_result = await db.execute(
            select(func.count(Group.id)).where(Group.owner_id == user.id)
        )
        group_count = group_count_result.scalar() or 0

        result.append(
            AdminUserListResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                is_admin=user.is_admin,
                created_at=user.created_at,
                recipe_count=recipe_count,
                calendar_count=calendar_count,
                group_count=group_count,
            )
        )

    return result


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_details(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> User:
    """Get detailed information about a specific user."""

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> User:
    """Update user details (admin only)."""

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin

    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_result = await db.execute(
            select(User).where(User.email == user_update.email, User.id != user_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )
        user.email = user_update.email

    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Soft delete a user (admin only)."""
    from datetime import datetime

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prevent deleting yourself
    if user.id == _admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account"
        )

    user.deleted_at = datetime.utcnow()
    await db.commit()


@router.get("/recipes")
async def list_all_recipes(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    category: str | None = None,
    difficulty: str | None = None,
    visibility: str | None = None,
):
    """List all recipes with details and filters (admin only)."""
    from sqlalchemy.orm import selectinload

    stmt = select(Recipe).where(Recipe.deleted_at.is_(None)).options(selectinload(Recipe.owner))

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Recipe.title.ilike(search_pattern),
                Recipe.description.ilike(search_pattern),
            )
        )

    if category:
        stmt = stmt.where(Recipe.category == category)

    if difficulty:
        stmt = stmt.where(Recipe.difficulty == difficulty)

    if visibility:
        stmt = stmt.where(Recipe.visibility == visibility)

    result = await db.execute(stmt.offset(skip).limit(limit))
    recipes = result.scalars().all()

    return [
        {
            "id": recipe.id,
            "title": recipe.title,
            "description": recipe.description,
            "owner_id": recipe.owner_id,
            "owner_username": recipe.owner.username,
            "visibility": recipe.visibility,
            "group_id": recipe.group_id,
            "serving_size": recipe.serving_size,
            "prep_time": recipe.prep_time,
            "cook_time": recipe.cook_time,
            "difficulty": recipe.difficulty,
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at,
        }
        for recipe in recipes
    ]


@router.get("/recipes/{recipe_id}")
async def get_recipe_details(
    recipe_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
):
    """Get detailed information about a specific recipe (admin only)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id, Recipe.deleted_at.is_(None))
        .options(selectinload(Recipe.owner))
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "owner_id": recipe.owner_id,
        "owner_username": recipe.owner.username,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "image_url": recipe.image_url,
        "serving_size": recipe.serving_size,
        "prep_time": recipe.prep_time,
        "cook_time": recipe.cook_time,
        "difficulty": recipe.difficulty,
        "nutritional_info": recipe.nutritional_info,
        "visibility": recipe.visibility,
        "group_id": recipe.group_id,
        "created_at": recipe.created_at,
        "updated_at": recipe.updated_at,
    }


@router.patch("/recipes/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> Recipe:
    """Update a recipe (admin only). Admins can modify all recipe fields."""

    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.deleted_at.is_(None))
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Update all fields from RecipeUpdate schema
    update_data = recipe_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recipe, field, value)

    await db.commit()

    # Re-fetch recipe with relationships eagerly loaded to avoid async lazy-load errors
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id, Recipe.deleted_at.is_(None))
        .options(selectinload(Recipe.owner), selectinload(Recipe.tags))
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Clean malformed ingredient data to satisfy response schema
    try:
        from app.api.v1.endpoints.recipes import clean_ingredient_data

        if recipe.ingredients:
            recipe.ingredients = clean_ingredient_data(recipe.ingredients)
    except Exception:
        # If cleaning fails, leave as-is and let response validation handle errors
        pass

    return recipe


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a recipe (admin only)."""
    from datetime import datetime

    result = await db.execute(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.deleted_at.is_(None))
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    recipe.deleted_at = datetime.utcnow()
    await db.commit()


# Calendar Management Endpoints
@router.get("/calendars")
async def list_all_calendars(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100,
):
    """List all calendars with details (admin only)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Calendar).options(selectinload(Calendar.owner)).offset(skip).limit(limit)
    )
    calendars = result.scalars().all()

    return [
        {
            "id": calendar.id,
            "name": calendar.name,
            "owner_id": calendar.owner_id,
            "owner_username": calendar.owner.username,
            "visibility": calendar.visibility,
            "group_id": calendar.group_id,
            "created_at": calendar.created_at,
            "updated_at": calendar.updated_at,
        }
        for calendar in calendars
    ]


@router.get("/calendars/{calendar_id}")
async def get_calendar_details(
    calendar_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
):
    """Get detailed information about a specific calendar (admin only)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Calendar)
        .where(Calendar.id == calendar_id)
        .options(selectinload(Calendar.owner), selectinload(Calendar.meals))
    )
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")

    return {
        "id": calendar.id,
        "name": calendar.name,
        "owner_id": calendar.owner_id,
        "owner_username": calendar.owner.username,
        "visibility": calendar.visibility,
        "group_id": calendar.group_id,
        "meal_count": len(calendar.meals),
        "created_at": calendar.created_at,
        "updated_at": calendar.updated_at,
    }


@router.patch("/calendars/{calendar_id}")
async def update_calendar(
    calendar_id: int,
    calendar_data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
):
    """Update a calendar (admin only)."""

    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")

    # Update allowed fields
    for field in ["name", "visibility", "group_id"]:
        if field in calendar_data:
            setattr(calendar, field, calendar_data[field])

    await db.commit()
    await db.refresh(calendar)

    return {
        "id": calendar.id,
        "name": calendar.name,
        "owner_id": calendar.owner_id,
        "visibility": calendar.visibility,
        "group_id": calendar.group_id,
    }


@router.delete("/calendars/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    calendar_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a calendar (admin only)."""

    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar not found")

    await db.delete(calendar)
    await db.commit()


# Group Management Endpoints
@router.get("/groups")
async def list_all_groups(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 100,
):
    """List all groups with details (admin only)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Group)
        .options(selectinload(Group.owner), selectinload(Group.members))
        .offset(skip)
        .limit(limit)
    )
    groups = result.scalars().all()

    return [
        {
            "id": group.id,
            "name": group.name,
            "owner_id": group.owner_id,
            "owner_username": group.owner.username,
            "member_count": len(group.members),
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }
        for group in groups
    ]


@router.get("/groups/{group_id}")
async def get_group_details(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
):
    """Get detailed information about a specific group (admin only)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Group)
        .where(Group.id == group_id)
        .options(
            selectinload(Group.owner),
            selectinload(Group.members).selectinload(GroupMember.user),
            selectinload(Group.recipes),
            selectinload(Group.calendars),
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    return {
        "id": group.id,
        "name": group.name,
        "owner_id": group.owner_id,
        "owner_username": group.owner.username,
        "members": [
            {
                "id": member.id,
                "user_id": member.user_id,
                "username": member.user.username,
                "role": member.role,
                "permissions": member.permissions,
            }
            for member in group.members
        ],
        "recipe_count": len(group.recipes),
        "calendar_count": len(group.calendars),
        "created_at": group.created_at,
        "updated_at": group.updated_at,
    }


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: int,
    group_data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
):
    """Update a group (admin only)."""

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Update allowed fields
    if "name" in group_data:
        group.name = group_data["name"]

    await db.commit()
    await db.refresh(group)

    return {
        "id": group.id,
        "name": group.name,
        "owner_id": group.owner_id,
    }


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a group (admin only)."""

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    await db.delete(group)
    await db.commit()


# Group Member Management
@router.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: int,
    member_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Remove a member from a group (admin only)."""

    result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.id == member_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group member not found")

    await db.delete(member)
    await db.commit()


# Feature Toggle Management
@router.get("/feature-toggles", response_model=list[FeatureToggleResponse])
async def list_feature_toggles(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> list[FeatureToggleResponse]:
    """List all feature toggles (admin only)."""

    result = await db.execute(select(FeatureToggle))
    toggles = result.scalars().all()
    return [FeatureToggleResponse.model_validate(toggle) for toggle in toggles]


@router.get("/feature-toggles/{feature_key}", response_model=FeatureToggleResponse)
async def get_feature_toggle(
    feature_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> FeatureToggleResponse:
    """Get a specific feature toggle (admin only)."""

    result = await db.execute(select(FeatureToggle).where(FeatureToggle.feature_key == feature_key))
    toggle = result.scalar_one_or_none()
    if not toggle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feature toggle not found"
        )
    return FeatureToggleResponse.model_validate(toggle)


@router.post(
    "/feature-toggles", response_model=FeatureToggleResponse, status_code=status.HTTP_201_CREATED
)
async def create_feature_toggle(
    toggle_data: FeatureToggleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> FeatureToggleResponse:
    """Create a new feature toggle (admin only)."""

    # Check if toggle already exists
    existing = await db.execute(
        select(FeatureToggle).where(FeatureToggle.feature_key == toggle_data.feature_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feature toggle with this key already exists",
        )

    toggle = FeatureToggle(**toggle_data.model_dump())
    db.add(toggle)
    await db.commit()
    await db.refresh(toggle)
    return FeatureToggleResponse.model_validate(toggle)


@router.patch("/feature-toggles/{feature_key}", response_model=FeatureToggleResponse)
async def update_feature_toggle(
    feature_key: str,
    toggle_update: FeatureToggleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> FeatureToggleResponse:
    """Update a feature toggle (admin only)."""

    result = await db.execute(select(FeatureToggle).where(FeatureToggle.feature_key == feature_key))
    toggle = result.scalar_one_or_none()
    if not toggle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feature toggle not found"
        )

    update_data = toggle_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(toggle, key, value)

    await db.commit()
    await db.refresh(toggle)
    return FeatureToggleResponse.model_validate(toggle)


@router.delete("/feature-toggles/{feature_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_toggle(
    feature_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a feature toggle (admin only)."""

    result = await db.execute(select(FeatureToggle).where(FeatureToggle.feature_key == feature_key))
    toggle = result.scalar_one_or_none()
    if not toggle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feature toggle not found"
        )

    await db.delete(toggle)
    await db.commit()


# OpenAI Settings Management
@router.get("/openai-settings", response_model=OpenAISettingsResponse)
async def get_openai_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> OpenAISettingsResponse:
    """Get OpenAI settings (admin only, API key not included)."""

    result = await db.execute(select(OpenAISettings).where(OpenAISettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        # Create default settings if they don't exist
        settings = OpenAISettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    response = OpenAISettingsResponse.model_validate(settings)
    response.has_api_key = bool(settings.api_key)
    response.searxng_url = settings.searxng_url or "http://localhost:8085"
    return response


@router.patch("/openai-settings", response_model=OpenAISettingsResponse)
async def update_openai_settings(
    settings_update: OpenAISettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> OpenAISettingsResponse:
    """Update OpenAI settings (admin only)."""

    result = await db.execute(select(OpenAISettings).where(OpenAISettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = OpenAISettings(id=1)
        db.add(settings)

    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    await db.commit()
    await db.refresh(settings)
    response = OpenAISettingsResponse.model_validate(settings)
    response.has_api_key = bool(settings.api_key)
    response.searxng_url = settings.searxng_url or "http://localhost:8085"
    return response


@router.get("/openai-models", response_model=OpenAIModelsListResponse)
async def get_openai_models(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> OpenAIModelsListResponse:
    """Get list of available OpenAI models (admin only)."""
    from openai import AsyncOpenAI

    # Get API key from settings
    result = await db.execute(select(OpenAISettings).where(OpenAISettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings or not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key is not configured. Please update OpenAI settings first.",
        )

    try:
        client = AsyncOpenAI(api_key=settings.api_key)
        models_response = await client.models.list()

        # Filter for chat-capable models
        # Include GPT-4 variants, GPT-3.5, O-series, and other chat models
        chat_model_prefixes = [
            "gpt-4",  # GPT-4, GPT-4-turbo, GPT-4o, GPT-4o-mini, GPT-4.1, etc.
            "gpt-3.5",  # GPT-3.5-turbo variants
            "o1",  # o1, o1-mini, o1-preview
            "o3",  # o3 models
            "o4",  # o4 models
            "gpt-5",  # GPT-5 variants if they exist
            "chatgpt",  # chatgpt-4o-latest and similar
        ]

        # Exclude non-chat models
        exclude_patterns = [
            "whisper",
            "tts",
            "dall-e",
            "davinci",
            "babbage",
            "ada",
            "embedding",
            "moderation",
            "transcribe",
            "realtime",
            "audio",
            "image",
            "sora",
            "search",
            "codex",
            "oss",
        ]

        gpt_models = [
            OpenAIModelInfo(id=model.id, owned_by=model.owned_by, created=model.created)
            for model in models_response.data
            if (
                any(model.id.startswith(prefix) for prefix in chat_model_prefixes)
                and not any(pattern in model.id for pattern in exclude_patterns)
            )
        ]

        # Sort by ID for consistency (newest versions typically come first alphabetically)
        gpt_models.sort(key=lambda x: x.id, reverse=True)

        return OpenAIModelsListResponse(models=gpt_models)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve OpenAI models: {str(e)}",
        )


# Session Settings Management
@router.get("/session-settings", response_model=SessionSettingsResponse)
async def get_session_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> SessionSettingsResponse:
    """Get session TTL settings (admin only)."""

    result = await db.execute(select(SessionSettings).where(SessionSettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        # Create default settings if they don't exist
        settings = SessionSettings(id=1, session_ttl_value=90, session_ttl_unit="days")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return SessionSettingsResponse.model_validate(settings)


@router.patch("/session-settings", response_model=SessionSettingsResponse)
async def update_session_settings(
    settings_update: SessionSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _admin: Annotated[User, Depends(require_admin)],
) -> SessionSettingsResponse:
    """Update session TTL settings (admin only)."""

    result = await db.execute(select(SessionSettings).where(SessionSettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = SessionSettings(id=1)
        db.add(settings)

    update_data = settings_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    await db.commit()
    await db.refresh(settings)
    return SessionSettingsResponse.model_validate(settings)
