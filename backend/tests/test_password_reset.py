"""Test password reset functionality."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PasswordResetToken, User
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_forgot_password_flow(client: AsyncClient, db_session: AsyncSession):
    """Test complete forgot password flow."""
    # Create a test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("oldpassword"),
    )
    db_session.add(user)
    await db_session.commit()

    # Request password reset
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # In development mode, token is returned
    token = data.get("token")
    assert token is not None

    # Reset password with token
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password has been reset successfully"

    # Try to login with new password
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "newpassword123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_forgot_password_invalid_email(client: AsyncClient):
    """Test forgot password with non-existent email."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    # Should still return success for security
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Test reset password with invalid token."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token", "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_reset_password_used_token(client: AsyncClient, db_session: AsyncSession):
    """Test reset password with already used token."""
    from datetime import datetime, timedelta

    # Create a test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("password"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create a used token
    token = PasswordResetToken(
        user_id=user.id,
        token="used-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        used_at=datetime.utcnow(),
    )
    db_session.add(token)
    await db_session.commit()

    # Try to use the token
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "used-token", "new_password": "newpassword123"},
    )
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]
