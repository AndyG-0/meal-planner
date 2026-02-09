"""add kroger integration tables and feature toggles

Revision ID: k1l2m3n4o5p6
Revises: f4g5h6i7j8k9
Create Date: 2026-01-19 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "k1l2m3n4o5p6"
down_revision: str | None = "f4g5h6i7j8k9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create kroger_settings table
    op.create_table(
        "kroger_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("client_secret", sa.String(length=255), nullable=True),
        sa.Column("oauth_client_id", sa.String(length=255), nullable=True),
        sa.Column("oauth_client_secret", sa.String(length=255), nullable=True),
        sa.Column("redirect_uri", sa.String(length=500), nullable=True),
        sa.Column("base_url", sa.String(length=255), nullable=False, server_default="https://api.kroger.com"),
        sa.Column("environment", sa.String(length=50), nullable=False, server_default="production"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create kroger_user_locations table
    op.create_table(
        "kroger_user_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.String(length=20), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("location_address", sa.String(length=500), nullable=True),
        sa.Column("location_chain", sa.String(length=100), nullable=True),
        sa.Column("location_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_kroger_location"),
    )
    op.create_index("ix_kroger_user_locations_id", "kroger_user_locations", ["id"])
    op.create_index("ix_kroger_user_locations_user_id", "kroger_user_locations", ["user_id"])

    # Create kroger_user_auth table
    op.create_table(
        "kroger_user_auth",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_type", sa.String(length=50), nullable=False, server_default="Bearer"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("scope", sa.String(length=500), nullable=True),
        sa.Column("kroger_user_id", sa.String(length=255), nullable=True),
        sa.Column("kroger_email", sa.String(length=255), nullable=True),
        sa.Column("kroger_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_kroger_auth"),
    )
    op.create_index("ix_kroger_user_auth_id", "kroger_user_auth", ["id"])
    op.create_index("ix_kroger_user_auth_user_id", "kroger_user_auth", ["user_id"])

    # Add feature toggles for Kroger integration
    op.execute(  # type: ignore[attr-defined]
        """
        INSERT INTO feature_toggles (feature_key, feature_name, description, is_enabled, created_at, updated_at)
        SELECT 'kroger_product_search', 'Kroger Product Search', 'Enable Kroger catalog and location search for grocery lists', false, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM feature_toggles WHERE feature_key = 'kroger_product_search'
        )
        """
    )

    op.execute(  # type: ignore[attr-defined]
        """
        INSERT INTO feature_toggles (feature_key, feature_name, description, is_enabled, created_at, updated_at)
        SELECT 'kroger_shopping_cart', 'Kroger Shopping Cart', 'Enable Kroger cart and identity integration for shopping', false, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM feature_toggles WHERE feature_key = 'kroger_shopping_cart'
        )
        """
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index("ix_kroger_user_auth_user_id", "kroger_user_auth")
    op.drop_index("ix_kroger_user_auth_id", "kroger_user_auth")
    op.drop_index("ix_kroger_user_locations_user_id", "kroger_user_locations")
    op.drop_index("ix_kroger_user_locations_id", "kroger_user_locations")

    # Drop tables
    op.drop_table("kroger_user_auth")
    op.drop_table("kroger_user_locations")
    op.drop_table("kroger_settings")

    # Remove feature toggles
    op.execute(  # type: ignore[attr-defined]
        "DELETE FROM feature_toggles WHERE feature_key IN ('kroger_product_search', 'kroger_shopping_cart')"
    )
