"""Legal-entity schemas."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.constants import (
    LegalEntityRelationshipType,
    LegalEntityStatus,
    LegalEntityType,
)
from app.schemas.common import SoftDeleteRead, TimestampedRead


class LegalEntityCreate(BaseModel):
    organization_id: uuid.UUID
    legal_name: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    entity_type: LegalEntityType
    jurisdiction: str | None = Field(default=None, max_length=128)
    formation_date: date | None = None
    external_id: str | None = Field(default=None, max_length=255)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class LegalEntityUpdate(BaseModel):
    legal_name: str | None = Field(default=None, min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    status: LegalEntityStatus | None = None
    jurisdiction: str | None = Field(default=None, max_length=128)
    formation_date: date | None = None
    external_id: str | None = Field(default=None, max_length=255)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    extra_metadata: dict[str, Any] | None = None


class LegalEntityRead(SoftDeleteRead):
    organization_id: uuid.UUID
    legal_name: str
    display_name: str | None
    entity_type: LegalEntityType
    status: LegalEntityStatus
    jurisdiction: str | None
    formation_date: date | None
    external_id: str | None
    base_currency: str
    extra_metadata: dict[str, Any]


class LegalEntityRelationshipCreate(BaseModel):
    parent_entity_id: uuid.UUID
    child_entity_id: uuid.UUID
    relationship_type: LegalEntityRelationshipType
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_relationship(self) -> LegalEntityRelationshipCreate:
        if self.parent_entity_id == self.child_entity_id:
            raise ValueError("A legal entity cannot relate to itself")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self


class LegalEntityRelationshipRead(TimestampedRead):
    parent_entity_id: uuid.UUID
    child_entity_id: uuid.UUID
    relationship_type: LegalEntityRelationshipType
    effective_from: date
    effective_to: date | None
