"""Email service for sending emails via SendGrid."""

import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Mail, To

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid."""

    def __init__(self, api_key: str | None = None, from_email: str | None = None) -> None:
        """Initialize the SendGrid API client.

        Args:
            api_key: SendGrid API key. If None, uses the one from settings.
            from_email: From email address. If None, uses SMTP_FROM from settings.
        """
        key = api_key or settings.SENDGRID_API_KEY
        self.client = SendGridAPIClient(key) if key else None
        self.api_key = key
        self.from_email = from_email or settings.SMTP_FROM or "noreply@mealplanner.local"

    def is_configured(self) -> bool:
        """Check if SendGrid is configured."""
        return bool(self.client and self.api_key)

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str,
        user_name: str,
    ) -> bool:
        """Send a password reset email.

        Args:
            to_email: Recipient email address
            reset_link: The full password reset link (with token and base URL)
            user_name: User's name for personalization

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("SendGrid is not configured, cannot send password reset email")
            return False

        try:
            from_email = Email(self.from_email)
            to_email_obj = To(to_email)
            subject = "Password Reset Request"

            html_content = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hi {user_name},</p>
                    <p>We received a request to reset your password. Click the link below to reset it:</p>
                    <p><a href="{reset_link}">Reset Password</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                    <p>Best regards,<br>The Meal Planner Team</p>
                </body>
            </html>
            """

            plain_text_content = f"""
Password Reset Request

Hi {user_name},

We received a request to reset your password. Click the link below to reset it:

{reset_link}

This link will expire in 24 hours.

If you didn't request a password reset, you can safely ignore this email.

Best regards,
The Meal Planner Team
            """

            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=plain_text_content,
                html_content=html_content,
            )

            response = self.client.send(mail)

            if response.status_code in [200, 202]:
                logger.info("Password reset email sent successfully to %s", to_email)
                return True
            else:
                logger.error("Failed to send password reset email to %s: %s", to_email, response.status_code)
                return False

        except Exception as e:  # noqa: BLE001
            logger.error("Error sending password reset email to %s: %s", to_email, str(e))
            return False

    async def send_admin_password_email(
        self,
        to_email: str,
        temporary_password: str,
        user_name: str,
    ) -> bool:
        """Send an admin-set temporary password email.

        Args:
            to_email: Recipient email address
            temporary_password: The temporary password set by admin
            user_name: User's name for personalization

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("SendGrid is not configured, cannot send admin password email")
            return False

        try:
            from_email = Email(self.from_email)
            to_email_obj = To(to_email)
            subject = "Your Password Has Been Reset by Administrator"

            html_content = f"""
            <html>
                <body>
                    <h2>Password Reset by Administrator</h2>
                    <p>Hi {user_name},</p>
                    <p>An administrator has reset your password. Use the temporary password below to log in:</p>
                    <p><strong>Temporary Password:</strong> <code>{temporary_password}</code></p>
                    <p>You will be required to change this password after logging in.</p>
                    <p>If you didn't expect this, please contact an administrator.</p>
                    <p>Best regards,<br>The Meal Planner Team</p>
                </body>
            </html>
            """

            plain_text_content = f"""
Password Reset by Administrator

Hi {user_name},

An administrator has reset your password. Use the temporary password below to log in:

Temporary Password: {temporary_password}

You will be required to change this password after logging in.

If you didn't expect this, please contact an administrator.

Best regards,
The Meal Planner Team
            """

            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=plain_text_content,
                html_content=html_content,
            )

            response = self.client.send(mail)

            if response.status_code in [200, 202]:
                logger.info("Admin password email sent successfully to %s", to_email)
                return True
            else:
                logger.error("Failed to send admin password email to %s: %s", to_email, response.status_code)
                return False

        except Exception as e:  # noqa: BLE001
            logger.error("Error sending admin password email to %s: %s", to_email, str(e))
            return False


# Singleton instance
_email_service: EmailService | None = None


def get_email_service(api_key: str | None = None, from_email: str | None = None) -> EmailService:
    """Get the email service instance.

    Args:
        api_key: Optional SendGrid API key. If provided, creates a new instance with this key.
                If not provided, returns the singleton instance.
        from_email: Optional from email address. If provided, uses this as the sender.

    Returns:
        EmailService instance
    """
    global _email_service  # noqa: PLW0603
    if api_key is not None:
        # Return a new instance with the provided API key
        return EmailService(api_key=api_key, from_email=from_email)
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
