"""Mako template for migration scripts."""

"""add kroger app cart table

Revision ID: 530f7db47377
Revises: 7bb662f1da41
Create Date: 2026-01-24 18:53:30.233781

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '530f7db47377'
down_revision = '7bb662f1da41'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create kroger_app_cart table for in-app cart management
    op.create_table(
        'kroger_app_cart',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(length=100), nullable=False),
        sa.Column('upc', sa.String(length=50), nullable=False),
        sa.Column('product_name', sa.String(length=500), nullable=False),
        sa.Column('brand', sa.String(length=200), nullable=True),
        sa.Column('size', sa.String(length=100), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('fulfillment_type', sa.String(length=20), nullable=False, server_default='PICKUP'),
        sa.Column('grocery_list_item_name', sa.String(length=255), nullable=True),  # Link to grocery list item
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kroger_app_cart_user_id'), 'kroger_app_cart', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_kroger_app_cart_user_id'), table_name='kroger_app_cart')
    op.drop_table('kroger_app_cart')
