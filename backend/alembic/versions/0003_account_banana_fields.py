"""add currency, opening_balance, sum_in; remove parent_id

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop FK constraint on parent_id before dropping the column
    conn = op.get_bind()
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(conn)
    for fk in inspector.get_foreign_keys("accounts"):
        if fk["constrained_columns"] == ["parent_id"]:
            op.drop_constraint(fk["name"], "accounts", type_="foreignkey")
            break
    op.drop_column("accounts", "parent_id")
    op.add_column("accounts", sa.Column("currency", sa.String(10), nullable=False, server_default="CHF"))
    op.add_column("accounts", sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False, server_default="0.00"))
    op.add_column("accounts", sa.Column("sum_in", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "sum_in")
    op.drop_column("accounts", "opening_balance")
    op.drop_column("accounts", "currency")
    op.add_column("accounts", sa.Column("parent_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True))
