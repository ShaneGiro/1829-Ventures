"""Fund schemas."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.core.constants import FundStatus
from app.schemas.common import TimestampedRead


class FundBase(BaseModel):
    name: str
    fund_number: str | None = None
    vintage_year: int | None = None
    committed_capital: Decimal | None = None


class FundCreate(FundBase):
    status: FundStatus = FundStatus.ACTIVE


class FundUpdate(BaseModel):
    name: str | None = None
    fund_number: str | None = None
    vintage_year: int | None = None
    committed_capital: Decimal | None = None
    status: FundStatus | None = None


class FundRead(TimestampedRead, FundBase):
    status: FundStatus
    organization_id: uuid.UUID
    legal_entity_id: uuid.UUID | None
