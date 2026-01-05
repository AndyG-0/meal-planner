"""add user preferences and recipe categories

Revision ID: 8b2d4e7f9012
Revises: 9a1c3f5e6789
Create Date: 2025-12-31 00:01:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8b2d4e7f9012"
down_revision = "9a1c3f5e6789"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Add user preferences columns
    op.add_column("users", sa.Column("dietary_preferences", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("calorie_target", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("preferences", sa.JSON(), nullable=True))

    # Add recipe category column
    op.add_column("recipes", sa.Column("category", sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade database schema."""
    # Remove recipe category column
    op.drop_column("recipes", "category")

    # Remove user preferences columns
    op.drop_column("users", "preferences")
    op.drop_column("users", "calorie_target")
    op.drop_column("users", "dietary_preferences")
