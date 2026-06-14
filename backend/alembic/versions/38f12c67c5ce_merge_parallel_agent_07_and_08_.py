"""merge parallel agent 07 and 08 migrations

Revision ID: 38f12c67c5ce
Revises: 7a8f1b2c3d4e, 8f3c2b71e4a9
Create Date: 2026-06-14 19:45:27.383793
"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '38f12c67c5ce'
down_revision: str | None = ('7a8f1b2c3d4e', '8f3c2b71e4a9')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
