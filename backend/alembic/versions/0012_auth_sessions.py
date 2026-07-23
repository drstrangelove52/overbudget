"""add auth_sessions table, replacing JWT with server-side sessions

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-23
"""
import sqlalchemy as sa
from alembic import op

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'auth_sessions',
        sa.Column('token', sa.String(64), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('auth_sessions')
