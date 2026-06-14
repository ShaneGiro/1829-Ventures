"""Pipeline service unit tests."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.services.pipeline_service import monitor_company, next_business_day, pass_company


def test_next_business_day_skips_weekends() -> None:
    assert next_business_day(date(2026, 6, 12)) == date(2026, 6, 15)
    assert next_business_day(date(2026, 6, 15)) == date(2026, 6, 16)


@pytest.mark.asyncio
async def test_monitor_requires_future_next_check_date() -> None:
    with pytest.raises(ValidationError, match="next-check date"):
        await monitor_company(
            cast(AsyncSession, object()),
            company_id=uuid.uuid4(),
            next_check_date=datetime.now(UTC).date(),
            reason_tags=[],
            actor_id=None,
        )


@pytest.mark.asyncio
async def test_pass_requires_reason_tags_before_db_lookup() -> None:
    with pytest.raises(ValidationError, match="reason tag"):
        await pass_company(
            cast(AsyncSession, object()),
            company_id=uuid.uuid4(),
            reason_tags=[],
            notes=None,
        )
