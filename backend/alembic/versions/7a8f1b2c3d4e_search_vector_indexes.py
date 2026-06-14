"""search vector indexes

Revision ID: 7a8f1b2c3d4e
Revises: 4d6ffdeb3a50
Create Date: 2026-06-14 20:10:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a8f1b2c3d4e"
down_revision: str | None = "4d6ffdeb3a50"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_companies_search_fts
        ON companies USING gin (
            (
                setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(thesis_notes, '')), 'C')
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_interactions_search_fts
        ON interactions USING gin (
            (
                setweight(to_tsvector('english', coalesce(summary, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(body, '')), 'B')
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_deals_search_fts
        ON deals USING gin (
            (
                setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(thesis_fit_notes, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(decision_notes, '')), 'C')
            )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_companies_embedding_hnsw
        ON companies USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_interactions_embedding_hnsw
        ON interactions USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_interactions_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_companies_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_deals_search_fts")
    op.execute("DROP INDEX IF EXISTS ix_interactions_search_fts")
    op.execute("DROP INDEX IF EXISTS ix_companies_search_fts")
