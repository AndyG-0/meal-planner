"""Tests for auth endpoints such as setup and register."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_check_setup_required_initially(client: AsyncClient):
    resp = await client.get("/api/v1/auth/setup-required")
    assert resp.status_code == 200
    assert resp.json()["setup_required"] is True


@pytest.mark.asyncio
async def test_setup_initial_admin_and_conflict(client: AsyncClient, db_session: AsyncSession):
    # Create admin when no users exist
    resp = await client.post(
        "/api/v1/auth/setup-admin",
        json={"username": "first", "email": "first@example.com", "password": "password"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_admin"] is True

    # Trying again should fail
    resp = await client.post(
        "/api/v1/auth/setup-admin",
        json={"username": "second", "email": "second@example.com", "password": "password"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_register_conflict(client: AsyncClient, db_session: AsyncSession):
    user = User(
        username="existing",
        email="existing@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Conflict on username
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "existing", "email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 400

    # Conflict on email
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "new", "email": "existing@example.com", "password": "password123"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_me_email_conflict(client: AsyncClient, db_session: AsyncSession):
    # Create two users
    u1 = User(username="u1", email="u1@example.com", password_hash=get_password_hash("p"))
    u2 = User(username="u2", email="u2@example.com", password_hash=get_password_hash("p"))
    db_session.add_all([u1, u2])
    await db_session.commit()

    # Login as u1
    login = await client.post("/api/v1/auth/login", data={"username": "u1", "password": "p"})
    token = login.json()["access_token"]

    # Attempt to update u1's email to u2's email
    resp = await client.patch(
        "/api/v1/auth/me",
        json={"email": "u2@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
