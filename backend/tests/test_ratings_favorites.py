"""Test recipe ratings and favorites functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recipe, User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_rate_recipe(client: AsyncClient, db_session: AsyncSession):
    """Test rating a recipe."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create test recipe
    recipe = Recipe(
        title="Test Recipe",
        description="Test description",
        owner_id=user.id,
        ingredients=[{"name": "flour", "quantity": 2, "unit": "cup"}],
        instructions=["Mix ingredients", "Bake"],
    )
    db_session.add(recipe)
    await db_session.commit()

    # Get auth token
    token = create_access_token(data={"sub": str(user.id)})

    # Rate the recipe
    response = await client.post(
        f"/api/v1/recipes/{recipe.id}/ratings",
        json={"rating": 5, "review": "Excellent recipe!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["review"] == "Excellent recipe!"


@pytest.mark.asyncio
async def test_update_rating(client: AsyncClient, db_session: AsyncSession):
    """Test updating an existing rating."""
    # Create test user and recipe
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    recipe = Recipe(
        title="Test Recipe",
        description="Test description",
        owner_id=user.id,
        ingredients=[{"name": "flour", "quantity": 2, "unit": "cup"}],
        instructions=["Mix ingredients"],
    )
    db_session.add(recipe)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Create initial rating
    await client.post(
        f"/api/v1/recipes/{recipe.id}/ratings",
        json={"rating": 3, "review": "Good"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Update rating
    response = await client.post(
        f"/api/v1/recipes/{recipe.id}/ratings",
        json={"rating": 5, "review": "Actually excellent!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["review"] == "Actually excellent!"


@pytest.mark.asyncio
async def test_favorite_recipe(client: AsyncClient, db_session: AsyncSession):
    """Test adding recipe to favorites."""
    # Create test user and recipe
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    recipe = Recipe(
        title="Test Recipe",
        description="Test description",
        owner_id=user.id,
        ingredients=[{"name": "flour", "quantity": 2, "unit": "cup"}],
        instructions=["Mix ingredients"],
    )
    db_session.add(recipe)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Add to favorites
    response = await client.post(
        f"/api/v1/recipes/{recipe.id}/favorite",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_favorites(client: AsyncClient, db_session: AsyncSession):
    """Test listing favorite recipes."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create multiple recipes
    for i in range(3):
        recipe = Recipe(
            title=f"Recipe {i}",
            description=f"Description {i}",
            owner_id=user.id,
            ingredients=[{"name": "ingredient", "quantity": 1, "unit": "cup"}],
            instructions=["Step 1"],
        )
        db_session.add(recipe)

    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Add first recipe to favorites
    await client.post(
        "/api/v1/recipes/1/favorite",
        headers={"Authorization": f"Bearer {token}"},
    )

    # List favorites
    response = await client.get(
        "/api/v1/recipes/favorites",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    favorites = response.json()
    assert len(favorites) == 1
    assert favorites[0]["title"] == "Recipe 0"
