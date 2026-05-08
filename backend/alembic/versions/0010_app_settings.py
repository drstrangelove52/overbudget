"""add app_settings table for storing credentials

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-08
"""
import sqlalchemy as sa
from alembic import op

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('value', sa.Text, nullable=False),
    )


def downgrade():
    op.drop_table('app_settings')
