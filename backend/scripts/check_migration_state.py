"""Guard against the "stamped but tables missing" Alembic state.

The API container runs ``alembic upgrade head`` on startup. If ``alembic_version``
has been stamped to a revision but the real tables were never created (e.g. a
stamp ran before the schema existed, or the Postgres data volume was wiped while
the version row survived), ``upgrade head`` is a no-op and the app boots against
an empty schema — every query then fails with ``relation "..." does not exist``.

This script detects that mismatch and clears the stale stamp (equivalent to
``alembic stamp base``) so the subsequent ``alembic upgrade head`` rebuilds the
whole schema. It is safe to run on every startup:

- Fresh database (no ``alembic_version``): does nothing; upgrade creates schema.
- Healthy database (stamp + tables present): does nothing.
- Broken database (stamp present, tables missing): clears the stamp.

    python -m scripts.check_migration_state
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.database import sync_engine

# A table from the initial schema migration. If Alembic claims the DB is migrated
# but this table is absent, the stamp is stale and the schema was never built.
SENTINEL_TABLE = "users"
VERSION_TABLE = "alembic_version"


def check() -> bool:
    """Clear a stale Alembic stamp if the schema is missing. Returns True if reset."""
    tables = set(inspect(sync_engine).get_table_names())
    stamped = VERSION_TABLE in tables and _has_version_row()
    schema_present = SENTINEL_TABLE in tables

    if stamped and not schema_present:
        with sync_engine.begin() as conn:
            conn.execute(text(f"DELETE FROM {VERSION_TABLE}"))  # noqa: S608 - constant identifier
        print(
            "[migration-guard] alembic_version was stamped but core tables are missing; "
            "cleared the stamp so 'alembic upgrade head' can rebuild the schema."
        )
        return True

    print("[migration-guard] migration state OK.")
    return False


def _has_version_row() -> bool:
    with sync_engine.connect() as conn:
        return conn.execute(text(f"SELECT 1 FROM {VERSION_TABLE} LIMIT 1")).first() is not None


if __name__ == "__main__":
    check()
