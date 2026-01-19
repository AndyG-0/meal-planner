"""initialize sendgrid email feature toggle

Revision ID: f4g5h6i7j8k9
Revises: e3f4g5h6i7j8
Create Date: 2026-01-18 10:05:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4g5h6i7j8k9"
down_revision: str | None = "e3f4g5h6i7j8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Check if the feature toggle already exists
    op.execute(  # type: ignore[attr-defined]
        """
        INSERT INTO feature_toggles (feature_key, feature_name, description, is_enabled, created_at, updated_at)
        SELECT 'sendgrid_email', 'SendGrid Email', 'Enable password reset emails via SendGrid', false, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM feature_toggles WHERE feature_key = 'sendgrid_email'
        )
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Do nothing - leave the feature toggle in place

