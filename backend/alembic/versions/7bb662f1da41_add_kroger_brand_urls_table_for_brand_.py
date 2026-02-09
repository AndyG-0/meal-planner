"""Mako template for migration scripts."""

"""Add kroger_brand_urls table for brand-specific cart and checkout URLs

Revision ID: 7bb662f1da41
Revises: 1bfd389747e4
Create Date: 2026-01-24 17:58:50.815199

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7bb662f1da41'
down_revision = '1bfd389747e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create kroger_brand_urls table
    op.create_table(
        'kroger_brand_urls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('cart_url', sa.String(length=500), nullable=True),
        sa.Column('checkout_url', sa.String(length=500), nullable=True),
        sa.Column('certification_cart_url', sa.String(length=500), nullable=True),
        sa.Column('certification_checkout_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kroger_brand_urls_id'), 'kroger_brand_urls', ['id'], unique=False)
    op.create_index(op.f('ix_kroger_brand_urls_brand'), 'kroger_brand_urls', ['brand'], unique=True)


def downgrade() -> None:
    # Drop kroger_brand_urls table
    op.drop_index(op.f('ix_kroger_brand_urls_brand'), table_name='kroger_brand_urls')
    op.drop_index(op.f('ix_kroger_brand_urls_id'), table_name='kroger_brand_urls')
    op.drop_table('kroger_brand_urls')
