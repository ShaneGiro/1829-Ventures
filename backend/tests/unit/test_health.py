"""Smoke tests: the app boots and the liveness endpoint responds."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_liveness(client: AsyncClient, api_prefix: str) -> None:
    resp = await client.get(f"{api_prefix}/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_request_id_header_is_returned(client: AsyncClient, api_prefix: str) -> None:
    resp = await client.get(f"{api_prefix}/health")
    assert "X-Request-ID" in resp.headers


@pytest.mark.asyncio
async def test_openapi_schema_available(client: AsyncClient) -> None:
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"]
