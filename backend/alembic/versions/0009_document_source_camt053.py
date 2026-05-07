"""add camt053 to document source enum

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-07
"""
from alembic import op

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE documents MODIFY COLUMN source ENUM('camera','email','upload','mt940','csv','camt053') NOT NULL")


def downgrade():
    op.execute("ALTER TABLE documents MODIFY COLUMN source ENUM('camera','email','upload','mt940','csv') NOT NULL")
