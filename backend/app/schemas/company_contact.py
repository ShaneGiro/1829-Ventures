"""Company contact (company<->person link) schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class CompanyContactBase(BaseModel):
    company_id: uuid.UUID
    person_id: uuid.UUID
    is_primary: bool = False
    role: str | None = None


class CompanyContactCreate(CompanyContactBase):
    pass


class CompanyContactUpdate(BaseModel):
    is_primary: bool | None = None
    role: str | None = None


class CompanyContactRead(TimestampedRead, CompanyContactBase):
    pass
