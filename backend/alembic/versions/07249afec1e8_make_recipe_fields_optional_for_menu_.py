"""Mako template for migration scripts."""

"""make_recipe_fields_optional_for_menu_items

Revision ID: 07249afec1e8
Revises: b033c548ddc5
Create Date: 2026-01-10 12:37:43.429258

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '07249afec1e8'
down_revision = 'b033c548ddc5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make ingredients and instructions nullable to support minimal menu items
    # Only title remains required
    op.alter_column('recipes', 'ingredients',
                    existing_type=sa.JSON(),
                    nullable=True)
    op.alter_column('recipes', 'instructions',
                    existing_type=sa.JSON(),
                    nullable=True)


def downgrade() -> None:
    # Revert to required fields
    op.alter_column('recipes', 'ingredients',
                    existing_type=sa.JSON(),
                    nullable=False)
    op.alter_column('recipes', 'instructions',
                    existing_type=sa.JSON(),
                    nullable=False)
