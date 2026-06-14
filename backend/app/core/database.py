"""Dual SQLAlchemy engines.

The API runs on an async engine (asyncpg); Celery workers and Alembic run on a
sync engine (psycopg2). Workers never touch the async engine — async event loops
inside Celery's prefork workers are a reliable source of bugs.

  async engine  -> FastAPI request handlers   (get_async_session)
  sync engine   -> Celery workers + Alembic    (get_sync_session)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ─── Async engine (FastAPI) ───────────────────────────────────────────────────
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
)

# ─── Sync engine (Celery workers + Alembic) ───────────────────────────────────
sync_engine = create_engine(
    settings.sync_database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async session and closes it after the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Generator[Session, None, None]:
    """Sync session for Celery workers. Use as a context manager via contextlib."""
    session = SyncSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
