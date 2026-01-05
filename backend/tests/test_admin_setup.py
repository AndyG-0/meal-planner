"""Test admin setup functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


@pytest.mark.asyncio
async def test_setup_required_no_users(client: AsyncClient):
    """Test setup required returns true when no users exist."""
    response = await client.get("/api/v1/auth/setup-required")
    assert response.status_code == 200
    assert response.json()["setup_required"] is True


@pytest.mark.asyncio
async def test_setup_admin_creates_first_admin(client: AsyncClient, db_session: AsyncSession):
    """Test creating the first admin user."""
    response = await client.post(
        "/api/v1/auth/setup-admin",
        json={
            "username": "admin",
            "email": "admin@example.com",
            "password": "adminpassword",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "admin"
    assert data["is_admin"] is True

    # Verify user in database
    result = await db_session.execute(select(User).where(User.username == "admin"))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_admin is True


@pytest.mark.asyncio
async def test_setup_admin_fails_when_users_exist(client: AsyncClient, db_session: AsyncSession):
    """Test setup admin fails when users already exist."""
    from app.utils.auth import get_password_hash

    # Create a user
    user = User(
        username="existing",
        email="existing@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Try to setup admin
    response = await client.post(
        "/api/v1/auth/setup-admin",
        json={
            "username": "admin",
            "email": "admin@example.com",
            "password": "adminpassword",
        },
    )
    assert response.status_code == 400
    assert "already been completed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_setup_required_false_when_users_exist(client: AsyncClient, db_session: AsyncSession):
    """Test setup required returns false when users exist."""
    from app.utils.auth import get_password_hash

    # Create a user
    user = User(
        username="existing",
        email="existing@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.get("/api/v1/auth/setup-required")
    assert response.status_code == 200
    assert response.json()["setup_required"] is False
