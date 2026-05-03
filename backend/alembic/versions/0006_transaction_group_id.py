"""transaction group_id for split bookings

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('transactions', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_index('ix_transactions_group_id', 'transactions', ['group_id'])


def downgrade():
    op.drop_index('ix_transactions_group_id', table_name='transactions')
    op.drop_column('transactions', 'group_id')
