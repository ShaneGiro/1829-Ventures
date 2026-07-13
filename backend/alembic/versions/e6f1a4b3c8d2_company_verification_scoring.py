"""Add company verification and fit-scoring fields.

Revision ID: e6f1a4b3c8d2
Revises: d5e9f3a2b7c1
Create Date: 2026-07-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e6f1a4b3c8d2"
down_revision = "d5e9f3a2b7c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("alumni_founder_status", sa.String(16), server_default="unverified", nullable=False),
    )
    op.add_column("companies", sa.Column("alumni_founder_confidence", sa.Float(), nullable=True))
    op.add_column(
        "companies",
        sa.Column("alumni_founder_evidence", postgresql.JSONB(), server_default="{}", nullable=False),
    )
    op.add_column("companies", sa.Column("alumni_founder_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "companies",
        sa.Column("operational_status", sa.String(24), server_default="unverified", nullable=False),
    )
    op.add_column("companies", sa.Column("operational_confidence", sa.Float(), nullable=True))
    op.add_column(
        "companies",
        sa.Column("operational_evidence", postgresql.JSONB(), server_default="{}", nullable=False),
    )
    op.add_column("companies", sa.Column("operational_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("companies", sa.Column("rubric_fit_score", sa.Float(), nullable=True))
    op.add_column("companies", sa.Column("thesis_alignment_score", sa.Float(), nullable=True))
    op.add_column("companies", sa.Column("fit_score_confidence", sa.Float(), nullable=True))
    op.add_column(
        "companies",
        sa.Column("fit_score_reasons", postgresql.JSONB(), server_default="[]", nullable=False),
    )
    op.add_column("companies", sa.Column("fit_score_version", sa.String(32), nullable=True))
    op.add_column("companies", sa.Column("fit_scored_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_companies_alumni_founder_status", "companies", ["alumni_founder_status"])
    op.create_index("ix_companies_operational_status", "companies", ["operational_status"])


def downgrade() -> None:
    op.drop_index("ix_companies_operational_status", table_name="companies")
    op.drop_index("ix_companies_alumni_founder_status", table_name="companies")
    for column in (
        "fit_scored_at",
        "fit_score_version",
        "fit_score_reasons",
        "fit_score_confidence",
        "thesis_alignment_score",
        "rubric_fit_score",
        "operational_verified_at",
        "operational_evidence",
        "operational_confidence",
        "operational_status",
        "alumni_founder_verified_at",
        "alumni_founder_evidence",
        "alumni_founder_confidence",
        "alumni_founder_status",
    ):
        op.drop_column("companies", column)
