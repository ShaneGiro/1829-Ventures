"""Configurable pipeline stage schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import TimestampedRead


class DealStatusBase(BaseModel):
    name: str
    sort_order: int = 0
    color: str | None = None
    is_terminal: bool = False


class DealStatusCreate(DealStatusBase):
    pass


class DealStatusUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    color: str | None = None
    is_terminal: bool | None = None


class DealStatusRead(TimestampedRead, DealStatusBase):
    is_system: bool
