"""Test user preferences functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.auth import create_access_token, get_password_hash


@pytest.mark.asyncio
async def test_update_dietary_preferences(client: AsyncClient, db_session: AsyncSession):
    """Test updating dietary preferences."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Update dietary preferences
    response = await client.patch(
        "/api/v1/auth/me",
        json={"dietary_preferences": ["vegan", "gluten-free"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "vegan" in data["dietary_preferences"]
    assert "gluten-free" in data["dietary_preferences"]


@pytest.mark.asyncio
async def test_update_calorie_target(client: AsyncClient, db_session: AsyncSession):
    """Test updating calorie target."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Update calorie target
    response = await client.patch(
        "/api/v1/auth/me",
        json={"calorie_target": 2000},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["calorie_target"] == 2000


@pytest.mark.asyncio
async def test_update_user_preferences(client: AsyncClient, db_session: AsyncSession):
    """Test updating general user preferences."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id)})

    # Update preferences
    response = await client.patch(
        "/api/v1/auth/me",
        json={"preferences": {"calendar_start_day": "monday", "theme": "dark"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["preferences"]["calendar_start_day"] == "monday"
    assert data["preferences"]["theme"] == "dark"
