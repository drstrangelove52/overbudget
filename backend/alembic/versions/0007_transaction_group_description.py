"""transaction group_description

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('transactions', sa.Column('group_description', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('transactions', 'group_description')
