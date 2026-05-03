"""drop opening_balance from accounts

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("accounts", "opening_balance")


def downgrade() -> None:
    op.add_column("accounts", sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False, server_default="0.00"))
