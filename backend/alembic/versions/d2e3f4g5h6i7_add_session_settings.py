"""add session settings

Revision ID: d2e3f4g5h6i7
Revises: c1d2e3f4g5h6
Create Date: 2026-01-02 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2e3f4g5h6i7"
down_revision: str | None = "c1d2e3f4g5h6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create session_settings table
    op.create_table(
        "session_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_ttl_value", sa.Integer(), nullable=False, default=90),
        sa.Column("session_ttl_unit", sa.String(length=20), nullable=False, default="days"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Insert default settings
    op.execute(
        """
        INSERT INTO session_settings (id, session_ttl_value, session_ttl_unit)
        VALUES (1, 90, 'days')
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("session_settings")
