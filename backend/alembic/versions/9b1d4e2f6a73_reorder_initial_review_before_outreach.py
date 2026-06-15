"""Reorder pipeline stages: Initial Review before Outreach.

Updates sort_order on existing deal_statuses rows so the change to
SEED_DEAL_STATUSES also applies to databases that were seeded before it.

Revision ID: 9b1d4e2f6a73
Revises: 38f12c67c5ce
Create Date: 2026-06-15 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "9b1d4e2f6a73"
down_revision = "38f12c67c5ce"
branch_labels = None
depends_on = None

# (name, new sort_order) — Initial Review moved ahead of Outreach.
NEW_ORDER = [
    ("Initial Review", 1),
    ("Outreach", 2),
    ("Intro Meeting", 3),
    ("Diligence", 4),
    ("IC Review", 5),
    ("Term Sheet", 6),
    ("Closed/Invested", 7),
]

OLD_ORDER = [
    ("Outreach", 1),
    ("Intro Meeting", 2),
    ("Initial Review", 3),
    ("Diligence", 4),
    ("IC Review", 5),
    ("Term Sheet", 6),
    ("Closed/Invested", 7),
]


def _apply(order: list[tuple[str, int]]) -> None:
    for name, sort_order in order:
        op.execute(
            "UPDATE deal_statuses "
            f"SET sort_order = {sort_order} "
            f"WHERE lower(name) = lower('{name}')"
        )


def upgrade() -> None:
    _apply(NEW_ORDER)


def downgrade() -> None:
    _apply(OLD_ORDER)
