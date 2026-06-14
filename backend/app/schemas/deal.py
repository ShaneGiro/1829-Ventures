"""Deal/opportunity schemas."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.core.constants import InvestmentStatus
from app.schemas.common import SoftDeleteRead
from app.schemas.task import TaskRead


class DealBase(BaseModel):
    name: str | None = None
    round_type: str | None = None
    round_amount: Decimal | None = None
    round_currency: str | None = None
    round_date: date | None = None
    thesis_fit_notes: str | None = None
    decision_notes: str | None = None
    is_follow_on: bool = False


class DealCreate(DealBase):
    """Requires a company and an initial investment status; round details optional."""

    company_id: uuid.UUID
    investment_status: InvestmentStatus = InvestmentStatus.SOURCED


class DealUpdate(BaseModel):
    name: str | None = None
    investment_status: InvestmentStatus | None = None
    deal_status_id: uuid.UUID | None = None
    round_type: str | None = None
    round_amount: Decimal | None = None
    round_currency: str | None = None
    round_date: date | None = None
    thesis_fit_notes: str | None = None
    decision_notes: str | None = None


class DealRead(SoftDeleteRead, DealBase):
    company_id: uuid.UUID
    investment_status: InvestmentStatus
    deal_status_id: uuid.UUID | None = None


class ReviewNeededTaskRead(BaseModel):
    task: TaskRead


class TriageRequest(BaseModel):
    outcome: Literal["start_review", "monitor", "pass"]
    reason_tags: list[str] = []
    next_check_date: date | None = None
    notes: str | None = None


class TriageResponse(BaseModel):
    outcome: Literal["start_review", "monitor", "pass"]
    deal: DealRead
    task: TaskRead | None = None
