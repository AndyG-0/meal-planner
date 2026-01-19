"""Test email service functionality."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_email_service_not_configured():
    """Test email service when no API key is provided."""
    service = EmailService(api_key=None)
    assert not service.is_configured()


@pytest.mark.asyncio
async def test_email_service_configured():
    """Test email service when API key is provided."""
    service = EmailService(api_key="test-api-key")
    assert service.is_configured()


@pytest.mark.asyncio
async def test_send_password_reset_email_not_configured():
    """Test sending password reset email when service is not configured."""
    service = EmailService(api_key=None)
    result = await service.send_password_reset_email(
        to_email="test@example.com",
        reset_link="http://example.com/reset?token=123",
        user_name="Test User",
    )
    assert result is False


@pytest.mark.asyncio
async def test_send_password_reset_email_success():
    """Test successful sending of password reset email."""
    with patch("app.services.email_service.SendGridAPIClient") as mock_sg:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.send = MagicMock(return_value=mock_response)
        mock_sg.return_value = mock_client

        service = EmailService(api_key="test-api-key")
        result = await service.send_password_reset_email(
            to_email="test@example.com",
            reset_link="http://example.com/reset?token=123",
            user_name="Test User",
        )
        assert result is True
        mock_client.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_password_reset_email_failure():
    """Test failed sending of password reset email."""
    with patch("app.services.email_service.SendGridAPIClient") as mock_sg:
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.send = MagicMock(side_effect=Exception("SendGrid error"))
        mock_sg.return_value = mock_client

        service = EmailService(api_key="test-api-key")
        result = await service.send_password_reset_email(
            to_email="test@example.com",
            reset_link="http://example.com/reset?token=123",
            user_name="Test User",
        )
        assert result is False


@pytest.mark.asyncio
async def test_send_admin_password_email_not_configured():
    """Test sending admin password email when service is not configured."""
    service = EmailService(api_key=None)
    result = await service.send_admin_password_email(
        to_email="test@example.com",
        temporary_password="temp123",
        user_name="Test User",
    )
    assert result is False


@pytest.mark.asyncio
async def test_send_admin_password_email_success():
    """Test successful sending of admin password email."""
    with patch("app.services.email_service.SendGridAPIClient") as mock_sg:
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.send = MagicMock(return_value=mock_response)
        mock_sg.return_value = mock_client

        service = EmailService(api_key="test-api-key")
        result = await service.send_admin_password_email(
            to_email="test@example.com",
            temporary_password="temp123",
            user_name="Test User",
        )
        assert result is True
        mock_client.send.assert_called_once()


@pytest.mark.asyncio
async def test_send_admin_password_email_failure():
    """Test failed sending of admin password email."""
    with patch("app.services.email_service.SendGridAPIClient") as mock_sg:
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.send = MagicMock(side_effect=Exception("SendGrid error"))
        mock_sg.return_value = mock_client

        service = EmailService(api_key="test-api-key")
        result = await service.send_admin_password_email(
            to_email="test@example.com",
            temporary_password="temp123",
            user_name="Test User",
        )
        assert result is False
