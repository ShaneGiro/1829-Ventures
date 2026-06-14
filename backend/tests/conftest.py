"""Shared pytest fixtures.

Agent 01 provides an HTTP client fixture against the FastAPI app. DB-session and
auth-header fixtures are expanded by Agents 02/03 as models and auth land.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def api_prefix() -> str:
    from app.core.config import settings

    return settings.api_v1_prefix
