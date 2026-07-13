"""Add the document upload lifecycle status.

Revision ID: c4d8e2f1a6b9
Revises: b7c4d8e9f102
Create Date: 2026-07-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c4d8e2f1a6b9"
down_revision = "b7c4d8e9f102"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("status", sa.String(length=16), server_default="confirmed", nullable=False),
    )
    op.create_index("ix_documents_status", "documents", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_column("documents", "status")
