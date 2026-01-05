"""add_searxng_url_to_openai_settings

Revision ID: b033c548ddc5
Revises: d2e3f4g5h6i7
Create Date: 2026-01-03 19:16:01.905882

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b033c548ddc5"
down_revision = "d2e3f4g5h6i7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add searxng_url column to openai_settings table
    op.add_column(
        "openai_settings",
        sa.Column(
            "searxng_url",
            sa.String(length=255),
            nullable=True,
            server_default="http://localhost:8085",
        ),
    )


def downgrade() -> None:
    # Remove searxng_url column from openai_settings table
    op.drop_column("openai_settings", "searxng_url")
