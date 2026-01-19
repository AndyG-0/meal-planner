"""Tests for admin password reset and email settings endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailSettings, User
from app.utils.auth import create_access_token, get_password_hash, verify_password


@pytest.mark.asyncio
async def test_admin_reset_user_password_no_email(client: AsyncClient, db_session: AsyncSession):
    """Test admin resetting user password without sending email."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Create regular user
    user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=get_password_hash("oldpassword"),
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Reset password without email
    response = await client.post(
        f"/api/v1/admin/users/{user.id}/reset-password",
        json={
            "temporary_password": "newpassword123",
            "send_email": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Password reset" in data["message"]

    # Verify password was changed
    await db_session.refresh(user)
    assert verify_password("newpassword123", user.password_hash)
    assert user.force_password_change is True


@pytest.mark.asyncio
async def test_admin_reset_user_password_with_email(client: AsyncClient, db_session: AsyncSession):
    """Test admin resetting user password and sending email."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Create regular user
    user = User(
        username="testuser",
        email="testuser@example.com",
        password_hash=get_password_hash("oldpassword"),
    )
    db_session.add(user)
    await db_session.commit()

    # Create email settings
    email_settings = EmailSettings(
        id=1,
        admin_email="admin@test.com",
        sendgrid_api_key="test-api-key",
    )
    db_session.add(email_settings)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Mock the email service
    with patch("app.api.v1.endpoints.admin.get_email_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.is_configured.return_value = True
        mock_service.send_admin_password_email.return_value = True
        mock_get_service.return_value = mock_service

        # Reset password with email
        response = await client.post(
            f"/api/v1/admin/users/{user.id}/reset-password",
            json={
                "temporary_password": "newpassword123",
                "send_email": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Password reset" in data["message"]


@pytest.mark.asyncio
async def test_admin_reset_user_password_not_found(client: AsyncClient, db_session: AsyncSession):
    """Test admin resetting password for non-existent user."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Try to reset password for non-existent user
    response = await client.post(
        "/api/v1/admin/users/99999/reset-password",
        json={
            "temporary_password": "newpassword123",
            "send_email": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_email_settings(client: AsyncClient, db_session: AsyncSession):
    """Test getting email settings."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Create email settings
    email_settings = EmailSettings(
        id=1,
        admin_email="admin@test.com",
        sendgrid_api_key="test-api-key",
    )
    db_session.add(email_settings)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Get email settings
    response = await client.get(
        "/api/v1/admin/email-settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["admin_email"] == "admin@test.com"
    assert data["has_sendgrid_key"] is True


@pytest.mark.asyncio
async def test_get_email_settings_no_settings(client: AsyncClient, db_session: AsyncSession):
    """Test getting email settings when none exist."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Get email settings (should return default)
    response = await client.get(
        "/api/v1/admin/email-settings",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "admin_email" in data


@pytest.mark.asyncio
async def test_update_email_settings(client: AsyncClient, db_session: AsyncSession):
    """Test updating email settings."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Create email settings
    email_settings = EmailSettings(
        id=1,
        admin_email="old@test.com",
        sendgrid_api_key="old-key",
    )
    db_session.add(email_settings)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Update email settings
    response = await client.patch(
        "/api/v1/admin/email-settings",
        json={
            "admin_email": "new@test.com",
            "sendgrid_api_key": "new-key",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["admin_email"] == "new@test.com"
    assert data["has_sendgrid_key"] is True


@pytest.mark.asyncio
async def test_update_email_settings_partial(client: AsyncClient, db_session: AsyncSession):
    """Test partially updating email settings."""
    # Create admin user
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=get_password_hash("password"),
        is_admin=True,
    )
    db_session.add(admin)
    await db_session.commit()

    # Create email settings
    email_settings = EmailSettings(
        id=1,
        admin_email="old@test.com",
        sendgrid_api_key="old-key",
    )
    db_session.add(email_settings)
    await db_session.commit()

    token = create_access_token(data={"sub": str(admin.id)})

    # Update only admin email
    response = await client.patch(
        "/api/v1/admin/email-settings",
        json={
            "admin_email": "new@test.com",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["admin_email"] == "new@test.com"
