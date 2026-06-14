"""Analytics service and route tests."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.core.constants import Role
from app.core.database import get_async_session
from app.core.dependencies import get_current_human_user
from app.main import app
from app.models.user import User
from app.schemas.analytics import CountByKey, PipelineSummary
from app.services import analytics_service


@pytest.mark.asyncio
async def test_pipeline_summary_excludes_unreviewed_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        analytics_service.analytics_repo,
        "counts_by_relationship_status",
        AsyncMock(return_value=[CountByKey(key="active", count=2)]),
    )
    monkeypatch.setattr(
        analytics_service.analytics_repo,
        "counts_by_investment_status",
        AsyncMock(return_value=[CountByKey(key="diligence", count=1)]),
    )
    count_companies = AsyncMock(return_value=2)
    monkeypatch.setattr(analytics_service.analytics_repo, "count_companies", count_companies)
    monkeypatch.setattr(analytics_service.analytics_repo, "count_deals", AsyncMock(return_value=1))

    summary = await analytics_service.get_pipeline_summary(AsyncMock())

    assert summary.total_companies == 2
    count_companies.assert_awaited_once()
    assert count_companies.await_args.kwargs["include_unreviewed"] is False


@pytest.mark.asyncio
async def test_portfolio_summary_accepts_optional_fund_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fund_id = uuid.uuid4()
    totals = {
        "total_investments": 1,
        "total_invested_amount": Decimal("1000"),
        "total_valuation_mark": Decimal("2000"),
        "average_tvpi": Decimal("2"),
        "average_dpi": None,
        "average_irr": None,
    }
    portfolio_totals = AsyncMock(return_value=totals)
    portfolio_by_fund = AsyncMock(return_value=[])
    monkeypatch.setattr(analytics_service.analytics_repo, "portfolio_totals", portfolio_totals)
    monkeypatch.setattr(analytics_service.analytics_repo, "portfolio_by_fund", portfolio_by_fund)

    summary = await analytics_service.get_portfolio_summary(AsyncMock(), fund_id=fund_id)

    assert summary.total_invested_amount == Decimal("1000")
    assert portfolio_totals.await_args.kwargs["fund_id"] == fund_id
    assert portfolio_by_fund.await_args.kwargs["fund_id"] == fund_id


@pytest.mark.asyncio
async def test_analytics_pipeline_endpoint(client: AsyncClient, api_prefix: str) -> None:
    user = User(
        id=uuid.uuid4(),
        email="member@g.rit.edu",
        role=Role.MEMBER,
        is_active=True,
        is_agent=False,
    )

    async def override_user() -> User:
        return user

    async def override_session() -> AsyncIterator[object]:
        yield object()

    async def fake_summary(
        _session: object, *, include_unreviewed: bool = False
    ) -> PipelineSummary:
        assert include_unreviewed is True
        return PipelineSummary(
            by_relationship_status=[CountByKey(key="review_needed", count=1)],
            by_investment_status=[],
            total_companies=1,
            total_deals=0,
        )

    app.dependency_overrides[get_current_human_user] = override_user
    app.dependency_overrides[get_async_session] = override_session
    original = analytics_service.get_pipeline_summary
    analytics_service.get_pipeline_summary = fake_summary
    try:
        response = await client.get(f"{api_prefix}/analytics/pipeline?include_unreviewed=true")
    finally:
        app.dependency_overrides.clear()
        analytics_service.get_pipeline_summary = original

    assert response.status_code == 200
    assert response.json()["by_relationship_status"] == [{"key": "review_needed", "count": 1}]
