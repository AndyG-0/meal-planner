"""add force_password_change field to users

Revision ID: e3f4g5h6i7j8
Revises: add_blocked_domains
Create Date: 2026-01-18 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f4g5h6i7j8"
down_revision: str | None = "add_blocked_domains"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add force_password_change column to users table
    op.add_column(
        "users",
        sa.Column(
            "force_password_change",
            sa.Boolean(),
            nullable=False,
            default=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column("users", "force_password_change")
