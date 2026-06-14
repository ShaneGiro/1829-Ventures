"""Portfolio metric schemas."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class PortfolioMetricBase(BaseModel):
    reporting_period: str | None = None
    reporting_date: date | None = None
    revenue: Decimal | None = None
    runway_months: Decimal | None = None
    headcount: int | None = None
    valuation_mark: Decimal | None = None
    tvpi: Decimal | None = None
    dpi: Decimal | None = None
    irr: Decimal | None = None


class PortfolioMetricCreate(PortfolioMetricBase):
    company_id: uuid.UUID
    investment_id: uuid.UUID | None = None


class PortfolioMetricUpdate(PortfolioMetricBase):
    pass


class PortfolioMetricRead(TimestampedRead, PortfolioMetricBase):
    company_id: uuid.UUID
    investment_id: uuid.UUID | None = None
