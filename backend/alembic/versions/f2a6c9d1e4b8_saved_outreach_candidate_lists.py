"""Add saved outreach candidate lists.

Revision ID: f2a6c9d1e4b8
Revises: e6f1a4b3c8d2
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2a6c9d1e4b8"
down_revision: str | None = "e6f1a4b3c8d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "outreach_candidate_lists",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column(
            "default_filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "change_history",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_outreach_candidate_lists_created_by_id",
        "outreach_candidate_lists",
        ["created_by_id"],
    )
    op.create_index(
        "ix_outreach_candidate_lists_owner_id", "outreach_candidate_lists", ["owner_id"]
    )
    op.create_index(
        "ix_outreach_candidate_lists_status", "outreach_candidate_lists", ["status"]
    )

    op.create_table(
        "outreach_candidate_list_items",
        sa.Column("list_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_status", sa.String(length=24), server_default="new", nullable=False),
        sa.Column("rank_score", sa.Float(), nullable=True),
        sa.Column(
            "rank_reasons",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("score_version", sa.String(length=32), nullable=True),
        sa.Column(
            "score_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("why_this_company", sa.Text(), nullable=True),
        sa.Column(
            "change_history",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["list_id"], ["outreach_candidate_lists.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "list_id", "company_id", name="uq_outreach_candidate_item_company"
        ),
    )
    op.create_index(
        "ix_outreach_candidate_list_items_assigned_to_id",
        "outreach_candidate_list_items",
        ["assigned_to_id"],
    )
    op.create_index(
        "ix_outreach_candidate_list_items_candidate_status",
        "outreach_candidate_list_items",
        ["candidate_status"],
    )
    op.create_index(
        "ix_outreach_candidate_list_items_company_id",
        "outreach_candidate_list_items",
        ["company_id"],
    )
    op.create_index(
        "ix_outreach_candidate_list_items_list_id",
        "outreach_candidate_list_items",
        ["list_id"],
    )
    op.create_index(
        "ix_outreach_candidate_list_items_person_id",
        "outreach_candidate_list_items",
        ["person_id"],
    )


def downgrade() -> None:
    op.drop_table("outreach_candidate_list_items")
    op.drop_table("outreach_candidate_lists")
