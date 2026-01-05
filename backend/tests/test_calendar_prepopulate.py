"""Tests for calendar prepopulation feature."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CalendarMeal, User


@pytest.mark.asyncio
async def test_prepopulate_calendar_week(
    client: AsyncClient,
    test_user: User,
    test_token: str,
    db_session: AsyncSession,
):
    """Test prepopulating a calendar for a week."""
    # Create a calendar
    calendar_data = {"name": "Test Calendar", "visibility": "private"}
    response = await client.post(
        "/api/v1/calendars",
        json=calendar_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 201
    calendar = response.json()
    calendar_id = calendar["id"]

    # Create some test recipes
    recipes = []
    for i, category in enumerate(["breakfast", "lunch", "dinner"]):
        recipe_data = {
            "title": f"Test {category.title()} Recipe {i}",
            "description": f"A test {category} recipe",
            "ingredients": [{"name": "ingredient", "quantity": 1, "unit": "cup"}],
            "instructions": ["Step 1", "Step 2"],
            "category": category,
        }
        response = await client.post(
            "/api/v1/recipes",
            json=recipe_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 201
        recipes.append(response.json())

    # Prepopulate the calendar
    start_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    prepopulate_data = {
        "start_date": start_date.isoformat(),
        "period": "week",
        "meal_types": ["breakfast", "lunch", "dinner"],
        "snacks_per_day": 0,
        "desserts_per_day": 0,
        "use_dietary_preferences": False,
        "avoid_duplicates": True,
    }

    response = await client.post(
        f"/api/v1/calendars/{calendar_id}/prepopulate",
        json=prepopulate_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )

    assert response.status_code == 201
    result = response.json()

    # Should create 21 meals (7 days * 3 meals)
    assert result["meals_created"] == 21
    assert "message" in result

    # Verify meals were created in the database
    meals_result = await db_session.execute(
        select(CalendarMeal).where(CalendarMeal.calendar_id == calendar_id)
    )
    meals = meals_result.scalars().all()
    assert len(meals) == 21


@pytest.mark.asyncio
async def test_prepopulate_calendar_with_snacks(
    client: AsyncClient,
    test_user: User,
    test_token: str,
    db_session: AsyncSession,
):
    """Test prepopulating a calendar with snacks."""
    # Create a calendar
    calendar_data = {"name": "Test Calendar 2", "visibility": "private"}
    response = await client.post(
        "/api/v1/calendars",
        json=calendar_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 201
    calendar = response.json()
    calendar_id = calendar["id"]

    # Create recipes for different categories
    categories = ["breakfast", "lunch", "dinner", "snack"]
    for i, category in enumerate(categories):
        recipe_data = {
            "title": f"Test {category.title()} Recipe {i}",
            "description": f"A test {category} recipe",
            "ingredients": [{"name": "ingredient", "quantity": 1, "unit": "cup"}],
            "instructions": ["Step 1"],
            "category": category,
        }
        response = await client.post(
            "/api/v1/recipes",
            json=recipe_data,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 201

    # Prepopulate with snacks
    start_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    prepopulate_data = {
        "start_date": start_date.isoformat(),
        "period": "day",
        "meal_types": ["breakfast", "lunch", "dinner"],
        "snacks_per_day": 2,
        "desserts_per_day": 0,
        "use_dietary_preferences": False,
        "avoid_duplicates": True,
    }

    response = await client.post(
        f"/api/v1/calendars/{calendar_id}/prepopulate",
        json=prepopulate_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )

    assert response.status_code == 201
    result = response.json()

    # Should create 5 meals (3 regular meals + 2 snacks)
    assert result["meals_created"] == 5


@pytest.mark.asyncio
async def test_prepopulate_calendar_no_recipes(
    client: AsyncClient,
    test_user: User,
    test_token: str,
):
    """Test prepopulating fails when no recipes exist."""
    # Create a calendar
    calendar_data = {"name": "Empty Calendar", "visibility": "private"}
    response = await client.post(
        "/api/v1/calendars",
        json=calendar_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 201
    calendar = response.json()
    calendar_id = calendar["id"]

    # Try to prepopulate without any recipes
    start_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    prepopulate_data = {
        "start_date": start_date.isoformat(),
        "period": "day",
        "meal_types": ["breakfast"],
        "snacks_per_day": 0,
        "desserts_per_day": 0,
        "use_dietary_preferences": False,
        "avoid_duplicates": True,
    }

    response = await client.post(
        f"/api/v1/calendars/{calendar_id}/prepopulate",
        json=prepopulate_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )

    assert response.status_code == 400
    assert "No recipes found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_prepopulate_calendar_invalid_meal_types(
    client: AsyncClient,
    test_user: User,
    test_token: str,
):
    """Test prepopulating with invalid meal types."""
    # Create a calendar
    calendar_data = {"name": "Test Calendar 3", "visibility": "private"}
    response = await client.post(
        "/api/v1/calendars",
        json=calendar_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 201
    calendar = response.json()
    calendar_id = calendar["id"]

    # Try to prepopulate with invalid meal type
    start_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    prepopulate_data = {
        "start_date": start_date.isoformat(),
        "period": "day",
        "meal_types": ["invalid_meal_type"],
        "snacks_per_day": 0,
        "desserts_per_day": 0,
        "use_dietary_preferences": False,
        "avoid_duplicates": True,
    }

    response = await client.post(
        f"/api/v1/calendars/{calendar_id}/prepopulate",
        json=prepopulate_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )

    # Should fail validation
    assert response.status_code == 422
