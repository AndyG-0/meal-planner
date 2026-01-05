"""add_feature_toggles

Revision ID: 88d249792ff0
Revises: 7b5f3021a5a0
Create Date: 2025-12-30 21:45:39.781994

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "88d249792ff0"
down_revision = "7b5f3021a5a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feature_toggles table
    op.create_table(
        "feature_toggles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feature_key", sa.String(length=100), nullable=False),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feature_key"),
    )
    op.create_index(
        op.f("ix_feature_toggles_feature_key"), "feature_toggles", ["feature_key"], unique=True
    )

    # Create openai_settings table
    op.create_table(
        "openai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_key", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=False, server_default="gpt-4"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Insert default feature toggle for AI recipes
    op.execute("""
        INSERT INTO feature_toggles (feature_key, feature_name, description, is_enabled, created_at)
        VALUES ('ai_recipe_creation', 'AI Recipe Creation', 'Enable AI-powered recipe creation using OpenAI', false, CURRENT_TIMESTAMP)
    """)

    # Insert default OpenAI settings
    op.execute("""
        INSERT INTO openai_settings (id, model, temperature, max_tokens, system_prompt)
        VALUES (1, 'gpt-4', 0.7, 2000, 'You are a helpful culinary assistant that helps users create and refine recipes. Your goal is to create detailed, practical recipes that users will love. When creating recipes, always provide complete information including ingredients with measurements, step-by-step instructions, prep time, cook time, and serving size. You can help with: creating random recipes, meal-specific recipes (breakfast, lunch, dinner, snacks), recipes with dietary restrictions (vegan, vegetarian, gluten-free, dairy-free, etc.), copycat recipes of popular dishes, and iterating on recipes based on user feedback. Always confirm recipe details with the user before adding or editing them in the database.')
    """)


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_toggles_feature_key"), table_name="feature_toggles")
    op.drop_table("openai_settings")
    op.drop_table("feature_toggles")
