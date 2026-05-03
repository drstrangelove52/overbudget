"""add csv to document source enum

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-02
"""
from alembic import op

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE documents MODIFY COLUMN source ENUM('camera','email','upload','mt940','csv') NOT NULL")


def downgrade():
    op.execute("ALTER TABLE documents MODIFY COLUMN source ENUM('camera','email','upload','mt940') NOT NULL")
