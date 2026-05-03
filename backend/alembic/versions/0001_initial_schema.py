"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("number", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column(
            "type",
            sa.Enum("asset", "liability", "equity", "income", "expense", name="accounttype"),
            nullable=False,
        ),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("iban", sa.String(34), nullable=True),
        sa.Column("is_internal", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="1"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "source",
            sa.Enum("camera", "email", "upload", "mt940", name="documentsource"),
            nullable=False,
        ),
        sa.Column("original_file", sa.String(500), nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("new", "processing", "pending", "booked", "error", name="documentstatus"),
            nullable=False,
            server_default="new",
        ),
        sa.Column("received_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "condition_field",
            sa.Enum("counterparty", "description", "amount", "iban", name="conditionfield"),
            nullable=False,
        ),
        sa.Column(
            "condition_operator",
            sa.Enum("contains", "equals", "lt", "gt", "regex", name="conditionoperator"),
            nullable=False,
        ),
        sa.Column("condition_value", sa.String(500), nullable=False),
        sa.Column("debit_account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("credit_account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("auto_confirm", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("learned_from_transaction_id", sa.Integer, nullable=True),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("date", sa.Date, nullable=False, index=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("counterparty", sa.String(200), nullable=True),
        sa.Column("debit_account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("credit_account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("documents.id"), nullable=True),
        sa.Column(
            "status",
            sa.Enum("suggested", "confirmed", "booked", name="transactionstatus"),
            nullable=False,
            server_default="suggested",
        ),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("is_transfer", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("rule_id", sa.Integer, sa.ForeignKey("rules.id"), nullable=True),
        sa.Column("hash", sa.String(64), nullable=True, unique=True, index=True),
    )

    # FK from rules back to transactions (learned_from)
    op.create_foreign_key(
        "fk_rules_learned_from",
        "rules", "transactions",
        ["learned_from_transaction_id"], ["id"],
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "period",
            sa.Enum("monthly", "yearly", name="budgetperiod"),
            nullable=False,
        ),
        sa.Column("active", sa.Boolean, nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_table("budgets")
    op.drop_constraint("fk_rules_learned_from", "rules", type_="foreignkey")
    op.drop_table("transactions")
    op.drop_table("rules")
    op.drop_table("documents")
    op.drop_table("accounts")
    for enum_name in [
        "accounttype", "documentsource", "documentstatus",
        "transactionstatus", "conditionfield", "conditionoperator", "budgetperiod",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
