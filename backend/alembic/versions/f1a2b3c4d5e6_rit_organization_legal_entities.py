"""Add RIT organization and legal-entity foundations.

Revision ID: f1a2b3c4d5e6
Revises: e6f1a4b3c8d2
Create Date: 2026-07-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f1a2b3c4d5e6"
down_revision = "e6f1a4b3c8d2"
branch_labels = None
depends_on = None

RIT_ORGANIZATION_ID = "18290000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("institutional_owner", sa.String(255), nullable=True),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])
    op.execute(
        sa.text(
            """
            INSERT INTO organizations
                (id, name, slug, institutional_owner, base_currency, timezone, status)
            VALUES
                (:id, '1829 Ventures', 'rit-1829-ventures',
                 'Rochester Institute of Technology', 'USD', 'America/New_York', 'active')
            """
        ).bindparams(id=RIT_ORGANIZATION_ID)
    )

    op.create_table(
        "organization_memberships",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_member"),
    )
    op.create_index(
        "ix_organization_memberships_organization_id",
        "organization_memberships",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_memberships_user_id", "organization_memberships", ["user_id"]
    )
    op.execute(
        sa.text(
            """
            INSERT INTO organization_memberships
                (id, organization_id, user_id, role, is_active)
            SELECT gen_random_uuid(), :organization_id, id, role, is_active
            FROM users
            WHERE is_agent = false AND archived_at IS NULL
            """
        ).bindparams(organization_id=RIT_ORGANIZATION_ID)
    )

    op.create_table(
        "legal_entities",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("jurisdiction", sa.String(128), nullable=True),
        sa.Column("formation_date", sa.Date(), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("base_currency", sa.String(3), nullable=False),
        sa.Column(
            "extra_metadata",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "legal_name", name="uq_org_legal_entity_name"),
    )
    op.create_index("ix_legal_entities_organization_id", "legal_entities", ["organization_id"])
    op.create_index("ix_legal_entities_entity_type", "legal_entities", ["entity_type"])

    op.create_table(
        "legal_entity_relationships",
        sa.Column("parent_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["parent_entity_id"], ["legal_entities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["child_entity_id"], ["legal_entities.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_entity_id",
            "child_entity_id",
            "relationship_type",
            "effective_from",
            name="uq_legal_entity_relationship_version",
        ),
    )
    op.create_index(
        "ix_legal_entity_relationships_parent_entity_id",
        "legal_entity_relationships",
        ["parent_entity_id"],
    )
    op.create_index(
        "ix_legal_entity_relationships_child_entity_id",
        "legal_entity_relationships",
        ["child_entity_id"],
    )

    op.add_column(
        "funds", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "funds", sa.Column("legal_entity_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_funds_organization_id",
        "funds",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_funds_legal_entity_id",
        "funds",
        "legal_entities",
        ["legal_entity_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_funds_organization_id", "funds", ["organization_id"])
    op.create_unique_constraint("uq_funds_legal_entity_id", "funds", ["legal_entity_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO legal_entities
                (id, organization_id, legal_name, display_name, entity_type,
                 status, base_currency, extra_metadata)
            SELECT gen_random_uuid(), :organization_id, name, name, 'fund',
                   CASE WHEN status = 'closed' THEN 'inactive' ELSE 'active' END,
                   'USD', jsonb_build_object('migration_source', 'existing_fund')
            FROM funds
            """
        ).bindparams(organization_id=RIT_ORGANIZATION_ID)
    )
    op.execute(
        sa.text(
            """
            UPDATE funds AS f
            SET organization_id = :organization_id,
                legal_entity_id = le.id
            FROM legal_entities AS le
            WHERE le.organization_id = :organization_id
              AND le.entity_type = 'fund'
              AND le.legal_name = f.name
            """
        ).bindparams(organization_id=RIT_ORGANIZATION_ID)
    )
    op.alter_column("funds", "organization_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("uq_funds_legal_entity_id", "funds", type_="unique")
    op.drop_index("ix_funds_organization_id", table_name="funds")
    op.drop_constraint("fk_funds_legal_entity_id", "funds", type_="foreignkey")
    op.drop_constraint("fk_funds_organization_id", "funds", type_="foreignkey")
    op.drop_column("funds", "legal_entity_id")
    op.drop_column("funds", "organization_id")
    op.drop_table("legal_entity_relationships")
    op.drop_table("legal_entities")
    op.drop_table("organization_memberships")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
