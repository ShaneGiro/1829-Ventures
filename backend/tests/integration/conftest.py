"""Integration-test fixtures: a real Postgres-backed sync session.

These tests require the database from docker-compose (or CI services) and the
postgis + vector extensions. They are marked `integration` so they can be
deselected when no database is available: pytest -m "not integration".
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import Base


def _test_database_url() -> str:
    """Derive a dedicated test database URL, distinct from the dev database.

    These fixtures drop and recreate the entire schema, so they must NEVER run
    against the application database. We target ``<db>_test`` (e.g. ``crm`` ->
    ``crm_test``) so running the suite locally can't wipe local dev data.
    """
    base = make_url(settings.sync_database_url)
    if base.database and base.database.endswith("_test"):
        return base.render_as_string(hide_password=False)
    return base.set(database=f"{base.database}_test").render_as_string(hide_password=False)


def _ensure_database_exists(url_str: str) -> None:
    """Create the test database if it does not exist (via the maintenance DB)."""
    url = make_url(url_str)
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            ).first()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    test_url = _test_database_url()
    _ensure_database_exists(test_url)
    eng = create_engine(test_url)
    with eng.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
