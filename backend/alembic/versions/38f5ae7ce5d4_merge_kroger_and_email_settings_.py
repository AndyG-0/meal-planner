"""Mako template for migration scripts."""

"""merge kroger and email settings migrations

Revision ID: 38f5ae7ce5d4
Revises: b34c6205a914, k1l2m3n4o5p6
Create Date: 2026-01-19 10:17:01.827690

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38f5ae7ce5d4'
down_revision = ('b34c6205a914', 'k1l2m3n4o5p6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
