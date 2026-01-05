"""Add permissions system

Revision ID: 5f2a8b9c3d4e
Revises: 4ec61b644961
Create Date: 2025-12-30 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5f2a8b9c3d4e"
down_revision = "4ec61b644961"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema to add permissions system."""

    # Add is_admin column to users table
    op.add_column(
        "users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false")
    )

    # Add visibility and group_id columns to recipes table
    op.add_column(
        "recipes",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"),
    )
    op.add_column("recipes", sa.Column("group_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_recipes_group_id", "recipes", "groups", ["group_id"], ["id"])
    op.create_index("ix_recipes_visibility", "recipes", ["visibility"])

    # Add visibility column to calendars table
    op.add_column(
        "calendars",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"),
    )
    op.create_index("ix_calendars_visibility", "calendars", ["visibility"])

    # Add visibility and group_id columns to grocery_lists table
    op.add_column(
        "grocery_lists",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"),
    )
    op.add_column("grocery_lists", sa.Column("group_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_grocery_lists_group_id", "grocery_lists", "groups", ["group_id"], ["id"]
    )
    op.create_index("ix_grocery_lists_visibility", "grocery_lists", ["visibility"])

    # Migrate existing data from is_public/is_shared to visibility
    # For recipes: is_public=true -> visibility='public', is_shared=true -> visibility='group', else 'private'
    op.execute("""
        UPDATE recipes
        SET visibility = CASE
            WHEN is_public = true THEN 'public'
            WHEN is_shared = true THEN 'group'
            ELSE 'private'
        END
    """)

    # For calendars: is_shared=true -> visibility='group', else 'private'
    op.execute("""
        UPDATE calendars
        SET visibility = CASE
            WHEN is_shared = true THEN 'group'
            ELSE 'private'
        END
    """)


def downgrade() -> None:
    """Downgrade database schema to remove permissions system."""

    # Remove indexes
    op.drop_index("ix_grocery_lists_visibility", table_name="grocery_lists")
    op.drop_index("ix_calendars_visibility", table_name="calendars")
    op.drop_index("ix_recipes_visibility", table_name="recipes")

    # Remove foreign keys
    op.drop_constraint("fk_grocery_lists_group_id", "grocery_lists", type_="foreignkey")
    op.drop_constraint("fk_recipes_group_id", "recipes", type_="foreignkey")

    # Remove columns from grocery_lists
    op.drop_column("grocery_lists", "group_id")
    op.drop_column("grocery_lists", "visibility")

    # Remove column from calendars
    op.drop_column("calendars", "visibility")

    # Remove columns from recipes
    op.drop_column("recipes", "group_id")
    op.drop_column("recipes", "visibility")

    # Remove column from users
    op.drop_column("users", "is_admin")
