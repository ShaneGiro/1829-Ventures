"""Analytics/dashboard response schemas.

Agent 02 ships generic shapes; Agent 08 extends with concrete dashboard models.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CountByKey(BaseModel):
    key: str
    count: int


class NumericByKey(BaseModel):
    key: str
    value: Decimal | None


class PipelineSummary(BaseModel):
    by_relationship_status: list[CountByKey]
    by_investment_status: list[CountByKey]
    total_companies: int
    total_deals: int


class PortfolioSummary(BaseModel):
    total_investments: int
    total_invested_amount: Decimal | None
    total_valuation_mark: Decimal | None
    average_tvpi: Decimal | None
    average_dpi: Decimal | None
    average_irr: Decimal | None
    by_fund: list[NumericByKey]


class InteractionCadencePoint(BaseModel):
    period: date
    count: int


class InteractionCadence(BaseModel):
    days: int
    points: list[InteractionCadencePoint]
    stale_company_count: int


class ThesisFitSummary(BaseModel):
    by_sector: list[CountByKey]
    by_rubric_bucket: list[CountByKey]
    rit_nexus: list[CountByKey]


class AgentActivitySummary(BaseModel):
    by_event_status: list[CountByKey]
    blocked_attempts_by_tool: list[CountByKey]
    trusted_writes_by_tool: list[CountByKey]
