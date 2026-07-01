"""Seed default deal pipeline stages.

Revision ID: b7c4d8e9f102
Revises: a3c7e9d21b54
Create Date: 2026-06-29 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "b7c4d8e9f102"
down_revision = "a3c7e9d21b54"
branch_labels = None
depends_on = None

DEFAULT_STATUSES = (
    ("18290000-0000-4000-8000-000000000001", "Initial Review", 1, False),
    ("18290000-0000-4000-8000-000000000002", "Outreach", 2, False),
    ("18290000-0000-4000-8000-000000000003", "Intro Meeting", 3, False),
    ("18290000-0000-4000-8000-000000000004", "Diligence", 4, False),
    ("18290000-0000-4000-8000-000000000005", "IC Review", 5, False),
    ("18290000-0000-4000-8000-000000000006", "Term Sheet", 6, False),
    ("18290000-0000-4000-8000-000000000007", "Closed/Invested", 7, True),
)


def upgrade() -> None:
    for status_id, name, sort_order, is_terminal in DEFAULT_STATUSES:
        op.execute(
            f"""
            INSERT INTO deal_statuses (
                id,
                name,
                sort_order,
                color,
                is_system,
                is_terminal,
                created_at,
                updated_at
            )
            VALUES (
                '{status_id}',
                '{name}',
                {sort_order},
                NULL,
                TRUE,
                {'TRUE' if is_terminal else 'FALSE'},
                now(),
                now()
            )
            ON CONFLICT (name) DO UPDATE
            SET sort_order = EXCLUDED.sort_order,
                is_system = TRUE,
                is_terminal = EXCLUDED.is_terminal,
                updated_at = now()
            WHERE deal_statuses.is_system = TRUE
               OR deal_statuses.name = EXCLUDED.name
            """
        )


def downgrade() -> None:
    names = ", ".join(f"'{name}'" for _, name, _, _ in DEFAULT_STATUSES)
    op.execute(f"DELETE FROM deal_statuses WHERE is_system = TRUE AND name IN ({names})")
