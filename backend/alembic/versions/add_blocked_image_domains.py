"""add blocked image domains table

Revision ID: add_blocked_domains
Revises: 07249afec1e8
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_blocked_domains'
down_revision = '07249afec1e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'blocked_image_domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_blocked_image_domains_domain', 'blocked_image_domains', ['domain'])


def downgrade() -> None:
    op.drop_index('ix_blocked_image_domains_domain')
    op.drop_table('blocked_image_domains')
