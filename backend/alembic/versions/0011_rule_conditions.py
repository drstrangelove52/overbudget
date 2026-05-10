"""replace single rule condition with rule_conditions table

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-10
"""
import sqlalchemy as sa
from alembic import op

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'rule_conditions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('rule_id', sa.Integer, sa.ForeignKey('rules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('field', sa.Enum('counterparty', 'description', 'amount', 'iban'), nullable=False),
        sa.Column('operator', sa.Enum('contains', 'equals', 'lt', 'gt', 'regex'), nullable=False),
        sa.Column('value', sa.String(500), nullable=False),
    )

    op.execute("""
        INSERT INTO rule_conditions (rule_id, field, operator, value)
        SELECT id, condition_field, condition_operator, condition_value FROM rules
    """)

    op.add_column('rules', sa.Column(
        'condition_logic',
        sa.Enum('and', 'or'),
        nullable=False,
        server_default='and',
    ))

    op.drop_column('rules', 'condition_field')
    op.drop_column('rules', 'condition_operator')
    op.drop_column('rules', 'condition_value')


def downgrade():
    op.add_column('rules', sa.Column('condition_field', sa.Enum('counterparty', 'description', 'amount', 'iban'), nullable=True))
    op.add_column('rules', sa.Column('condition_operator', sa.Enum('contains', 'equals', 'lt', 'gt', 'regex'), nullable=True))
    op.add_column('rules', sa.Column('condition_value', sa.String(500), nullable=True))

    op.execute("""
        UPDATE rules r
        INNER JOIN (
            SELECT rule_id, field, operator, value
            FROM rule_conditions
            WHERE id IN (SELECT MIN(id) FROM rule_conditions GROUP BY rule_id)
        ) rc ON r.id = rc.rule_id
        SET r.condition_field = rc.field,
            r.condition_operator = rc.operator,
            r.condition_value = rc.value
    """)

    op.drop_column('rules', 'condition_logic')
    op.drop_table('rule_conditions')
