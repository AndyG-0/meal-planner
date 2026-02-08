"""Mako template for migration scripts."""

"""add_cart_url_to_kroger_settings

Revision ID: 1bfd389747e4
Revises: l2m3n4o5p6q7
Create Date: 2026-01-19 20:32:00.659609

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bfd389747e4'
down_revision = 'l2m3n4o5p6q7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add cart_url and certification_cart_url columns to kroger_settings table
    op.add_column('kroger_settings', sa.Column('cart_url', sa.String(length=500), nullable=True))
    op.add_column('kroger_settings', sa.Column('certification_cart_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Remove cart_url and certification_cart_url columns from kroger_settings table
    op.drop_column('kroger_settings', 'certification_cart_url')
    op.drop_column('kroger_settings', 'cart_url')
