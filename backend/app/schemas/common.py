"""Shared schema base classes and common response types."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for read schemas that serialize from SQLAlchemy models."""

    model_config = ConfigDict(from_attributes=True)


class TimestampedRead(ORMModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SoftDeleteRead(TimestampedRead):
    archived_at: datetime | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
