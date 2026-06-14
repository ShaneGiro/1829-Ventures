"""Analytics/dashboard response schemas.

Agent 02 ships generic shapes; Agent 08 extends with concrete dashboard models.
"""

from __future__ import annotations

from pydantic import BaseModel


class CountByKey(BaseModel):
    key: str
    count: int


class PipelineSummary(BaseModel):
    by_relationship_status: list[CountByKey]
    by_investment_status: list[CountByKey]
    total_companies: int
    total_deals: int
