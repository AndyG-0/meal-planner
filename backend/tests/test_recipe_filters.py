"""Test recipe search and filtering functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recipe, RecipeTag, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_filter_recipes_by_category(client: AsyncClient, db_session: AsyncSession):
    """Test filtering recipes by category."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create recipes with different categories
    breakfast = Recipe(
        title="Pancakes",
        description="Fluffy pancakes",
        owner_id=user.id,
        category="breakfast",
        ingredients=[{"name": "flour", "quantity": 2, "unit": "cup"}],
        instructions=["Mix", "Cook"],
    )
    dinner = Recipe(
        title="Steak",
        description="Grilled steak",
        owner_id=user.id,
        category="dinner",
        ingredients=[{"name": "steak", "quantity": 1, "unit": "lb"}],
        instructions=["Grill"],
    )
    db_session.add_all([breakfast, dinner])
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Filter by breakfast
    response = await client.get(
        "/api/v1/recipes?category=breakfast",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    recipes = response.json()
    if isinstance(recipes, dict):
        recipes = recipes.get("items", [])
    assert len(recipes) == 1
    assert recipes[0]["title"] == "Pancakes"


@pytest.mark.asyncio
async def test_filter_recipes_by_difficulty(client: AsyncClient, db_session: AsyncSession):
    """Test filtering recipes by difficulty."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create recipes with different difficulties
    easy = Recipe(
        title="Toast",
        owner_id=user.id,
        difficulty="easy",
        ingredients=[{"name": "bread", "quantity": 2, "unit": "slice"}],
        instructions=["Toast"],
    )
    hard = Recipe(
        title="Soufflé",
        owner_id=user.id,
        difficulty="hard",
        ingredients=[{"name": "eggs", "quantity": 4, "unit": "whole"}],
        instructions=["Complex step 1", "Complex step 2"],
    )
    db_session.add_all([easy, hard])
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Filter by easy
    response = await client.get(
        "/api/v1/recipes?difficulty=easy",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    recipes = response.json()
    if isinstance(recipes, dict):
        recipes = recipes.get("items", [])
    assert len(recipes) == 1
    assert recipes[0]["difficulty"] == "easy"


@pytest.mark.asyncio
async def test_filter_recipes_by_prep_time(client: AsyncClient, db_session: AsyncSession):
    """Test filtering recipes by maximum prep time."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create recipes with different prep times
    quick = Recipe(
        title="Quick Recipe",
        owner_id=user.id,
        prep_time=10,
        ingredients=[{"name": "ingredient", "quantity": 1, "unit": "cup"}],
        instructions=["Step 1"],
    )
    slow = Recipe(
        title="Slow Recipe",
        owner_id=user.id,
        prep_time=60,
        ingredients=[{"name": "ingredient", "quantity": 1, "unit": "cup"}],
        instructions=["Step 1"],
    )
    db_session.add_all([quick, slow])
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Filter by max 30 minutes
    response = await client.get(
        "/api/v1/recipes?max_prep_time=30",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    recipes = response.json()
    if isinstance(recipes, dict):
        recipes = recipes.get("items", [])
    assert len(recipes) == 1
    assert recipes[0]["prep_time"] == 10


@pytest.mark.asyncio
async def test_filter_recipes_by_dietary_tag(client: AsyncClient, db_session: AsyncSession):
    """Test filtering recipes by dietary tags."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create recipes
    vegan_recipe = Recipe(
        title="Vegan Salad",
        owner_id=user.id,
        ingredients=[{"name": "lettuce", "quantity": 1, "unit": "head"}],
        instructions=["Chop", "Serve"],
    )
    meat_recipe = Recipe(
        title="Beef Stew",
        owner_id=user.id,
        ingredients=[{"name": "beef", "quantity": 1, "unit": "lb"}],
        instructions=["Cook"],
    )
    db_session.add_all([vegan_recipe, meat_recipe])
    await db_session.commit()

    # Add tags
    vegan_tag = RecipeTag(recipe_id=vegan_recipe.id, tag_name="vegan")
    db_session.add(vegan_tag)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Filter by vegan
    response = await client.get(
        "/api/v1/recipes?dietary=vegan",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    recipes = response.json()
    if isinstance(recipes, dict):
        recipes = recipes.get("items", [])
    assert len(recipes) == 1
    assert recipes[0]["title"] == "Vegan Salad"
