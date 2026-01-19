"""Tests for calendar prepopulation with collections feature."""

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Calendar,
    CalendarMeal,
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    User,
)
from app.services.calendar_prepopulate import CalendarPrepopulateService
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_prepopulate_with_collection_filter(db_session: AsyncSession):
    """Test prepopulating a calendar using a specific collection."""
    # Create user and calendar
    user = User(username="u1", email="u1@example.com", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()

    calendar = Calendar(name="Cal", owner_id=user.id)
    db_session.add(calendar)
    await db_session.commit()

    # Create recipes for each meal type
    recipes = []
    for cat in ["breakfast", "lunch", "dinner"]:
        r = Recipe(
            title=f"{cat}",
            owner_id=user.id,
            category=cat,
            visibility="public",
            ingredients=[{"name": "i", "quantity": 1, "unit": "u"}],
            instructions=["a"],
        )
        recipes.append(r)
        db_session.add(r)
    await db_session.commit()

    # Create a collection and add recipes to it
    collection = RecipeCollection(
        name="Test Collection",
        description="A test collection",
        user_id=user.id,
    )
    db_session.add(collection)
    await db_session.commit()

    for recipe in recipes:
        item = RecipeCollectionItem(
            collection_id=collection.id,  # type: ignore[union-attr]
            recipe_id=recipe.id,  # type: ignore[union-attr]
        )
        db_session.add(item)
    await db_session.commit()

    # Prepopulate using the collection
    service = CalendarPrepopulateService(db_session)
    meals_created, end_date = await service.prepopulate_calendar(
        calendar.id,  # type: ignore[arg-type]
        user,
        datetime.now(),
        "week",
        ["breakfast", "lunch", "dinner"],
        snacks_per_day=0,
        desserts_per_day=0,
        use_dietary_preferences=False,
        avoid_duplicates=True,
        collection_id=collection.id,  # type: ignore[arg-type]
    )

    # Should create 21 meals (7 days * 3 meal types)
    assert meals_created == 21

    # Verify meals are from the collection
    result = await db_session.execute(
        select(CalendarMeal).where(CalendarMeal.calendar_id == calendar.id)
    )
    meals = result.scalars().all()
    assert len(meals) == 21

    collection_recipe_ids = {r.id for r in recipes}
    for meal in meals:
        assert meal.recipe_id in collection_recipe_ids


@pytest.mark.asyncio
async def test_prepopulate_collection_filters_by_category(db_session: AsyncSession):
    """Test that collection prepopulate only uses recipes of the correct category."""
    # Create user and calendar
    user = User(username="u2", email="u2@example.com", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()

    calendar = Calendar(name="Cal2", owner_id=user.id)
    db_session.add(calendar)
    await db_session.commit()

    # Create breakfast and lunch recipes
    breakfast_recipe = Recipe(
        title="Breakfast",
        owner_id=user.id,
        category="breakfast",
        visibility="public",
        ingredients=[{"name": "i", "quantity": 1, "unit": "u"}],
        instructions=["a"],
    )
    lunch_recipe = Recipe(
        title="Lunch",
        owner_id=user.id,
        category="lunch",
        visibility="public",
        ingredients=[{"name": "i", "quantity": 1, "unit": "u"}],
        instructions=["a"],
    )
    db_session.add(breakfast_recipe)
    db_session.add(lunch_recipe)
    await db_session.commit()

    # Create a collection with only breakfast recipe
    collection = RecipeCollection(
        name="Breakfast Collection",
        user_id=user.id,
    )
    db_session.add(collection)
    await db_session.commit()

    item = RecipeCollectionItem(
        collection_id=collection.id,
        recipe_id=breakfast_recipe.id,
    )
    db_session.add(item)
    await db_session.commit()

    # Try to prepopulate with lunch type from collection - should fail
    service = CalendarPrepopulateService(db_session)

    with pytest.raises(ValueError, match="No recipes found"):
        await service.prepopulate_calendar(
            calendar.id,  # type: ignore[arg-type]
            user,
            datetime.now(),
            "day",
            ["lunch"],
            snacks_per_day=0,
            desserts_per_day=0,
            use_dietary_preferences=False,
            avoid_duplicates=True,
            collection_id=collection.id,  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_prepopulate_with_invalid_collection_id(db_session: AsyncSession):
    """Test prepopulating with an invalid collection ID."""
    # Create user and calendar
    user = User(username="u3", email="u3@example.com", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()

    calendar = Calendar(name="Cal3", owner_id=user.id)
    db_session.add(calendar)
    await db_session.commit()

    # Create a simple recipe
    recipe = Recipe(
        title="Breakfast",
        owner_id=user.id,
        category="breakfast",
        visibility="public",
        ingredients=[{"name": "i", "quantity": 1, "unit": "u"}],
        instructions=["a"],
    )
    db_session.add(recipe)
    await db_session.commit()

    # Try to prepopulate with invalid collection ID
    service = CalendarPrepopulateService(db_session)

    with pytest.raises(ValueError, match="not found"):
        await service.prepopulate_calendar(
            calendar.id,  # type: ignore[arg-type]
            user,
            datetime.now(),
            "day",
            ["breakfast"],
            snacks_per_day=0,
            desserts_per_day=0,
            use_dietary_preferences=False,
            avoid_duplicates=True,
            collection_id=99999,
        )


@pytest.mark.asyncio
async def test_prepopulate_without_collection_still_works(db_session: AsyncSession):
    """Test that prepopulating without collection_id still works as before."""
    # Create user and calendar
    user = User(username="u4", email="u4@example.com", password_hash=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()

    calendar = Calendar(name="Cal4", owner_id=user.id)
    db_session.add(calendar)
    await db_session.commit()

    # Create recipes for each meal type
    recipes = []
    for cat in ["breakfast", "lunch", "dinner"]:
        r = Recipe(
            title=f"{cat}",
            owner_id=user.id,
            category=cat,
            visibility="public",
            ingredients=[{"name": "i", "quantity": 1, "unit": "u"}],
            instructions=["a"],
        )
        recipes.append(r)
        db_session.add(r)
    await db_session.commit()

    # Prepopulate without collection_id (should use all recipes)
    service = CalendarPrepopulateService(db_session)
    meals_created, end_date = await service.prepopulate_calendar(
        calendar.id,  # type: ignore[arg-type]
        user,
        datetime.now(),
        "day",
        ["breakfast", "lunch", "dinner"],
        snacks_per_day=0,
        desserts_per_day=0,
        use_dietary_preferences=False,
        avoid_duplicates=True,
        # collection_id is omitted
    )

    # Should create 3 meals (1 day * 3 meal types)
    assert meals_created == 3

    # Verify meals were created
    result = await db_session.execute(
        select(CalendarMeal).where(CalendarMeal.calendar_id == calendar.id)
    )
    meals = result.scalars().all()
    assert len(meals) == 3
