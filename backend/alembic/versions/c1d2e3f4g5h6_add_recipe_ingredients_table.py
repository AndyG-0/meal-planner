"""add recipe ingredients table

Revision ID: c1d2e3f4g5h6
Revises: b660a0cf8da0
Create Date: 2026-01-02 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4g5h6"
down_revision: str | None = "b660a0cf8da0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create recipe_ingredients table for handling staple recipes as ingredients
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_recipe_id", sa.Integer(), nullable=True),
        sa.Column("ingredient_name", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ingredient_recipe_id"], ["recipes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(ingredient_recipe_id IS NOT NULL) OR (ingredient_name IS NOT NULL)",
            name="check_ingredient_source",
        ),
    )
    op.create_index("ix_recipe_ingredients_recipe_id", "recipe_ingredients", ["recipe_id"])
    op.create_index(
        "ix_recipe_ingredients_ingredient_recipe_id", "recipe_ingredients", ["ingredient_recipe_id"]
    )

    # Update the category enum to use 'staple' instead of 'ingredient'
    # Note: This migration will preserve existing 'ingredient' values as 'staple'
    # PostgreSQL approach - need to handle existing data
    op.execute("""
        UPDATE recipes
        SET category = 'staple'
        WHERE category = 'ingredient'
    """)


def downgrade() -> None:
    # Revert category changes
    op.execute("""
        UPDATE recipes
        SET category = 'ingredient'
        WHERE category = 'staple'
    """)

    # Drop the recipe_ingredients table
    op.drop_index("ix_recipe_ingredients_ingredient_recipe_id", "recipe_ingredients")
    op.drop_index("ix_recipe_ingredients_recipe_id", "recipe_ingredients")
    op.drop_table("recipe_ingredients")
