"""Investment schemas."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.common import SoftDeleteRead


class InvestmentBase(BaseModel):
    round_name: str | None = None
    amount: Decimal | None = None
    currency: str | None = "USD"
    investment_date: date | None = None
    instrument: str | None = None
    pre_money_valuation: Decimal | None = None
    post_money_valuation: Decimal | None = None
    ownership_pct: Decimal | None = None


class InvestmentCreate(InvestmentBase):
    fund_id: uuid.UUID
    company_id: uuid.UUID
    deal_id: uuid.UUID | None = None


class InvestmentUpdate(InvestmentBase):
    fund_id: uuid.UUID | None = None


class InvestmentRead(SoftDeleteRead, InvestmentBase):
    fund_id: uuid.UUID
    company_id: uuid.UUID
    deal_id: uuid.UUID | None = None
    fund_name: str | None = None
    company_name: str | None = None
