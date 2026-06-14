"""Alembic migration environment.

Runs migrations on the SYNC engine (psycopg2) — Alembic is not async. The target
metadata comes from app.models so autogenerate sees every registered table.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.models import Base  # noqa: F401 - imported for metadata side effects

config = context.config

# Inject the sync database URL from app settings (alembic.ini leaves it blank).
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# PostGIS installs ~37 system/tiger/topology tables (spatial_ref_sys, edges, etc.)
# that are not part of our models. Without this filter autogenerate would try to
# create/drop them. We only manage tables present in our own metadata.
_POSTGIS_SYSTEM_TABLES = {"spatial_ref_sys"}


def include_name(name: str | None, type_: str, parent_names: dict[str, str | None]) -> bool:
    if type_ == "table":
        return name in target_metadata.tables and name not in _POSTGIS_SYSTEM_TABLES
    return True


# NOTE: autogenerate emits `geoalchemy2.types.*` and `pgvector.sqlalchemy.*` in the
# migration body but does not add the matching top-level imports. After running
# `alembic revision --autogenerate`, add these to the new migration's header:
#     import geoalchemy2
#     import pgvector.sqlalchemy


def run_migrations_offline() -> None:
    context.configure(
        url=settings.sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_name=include_name,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
