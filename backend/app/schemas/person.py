"""Person and affiliation schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr

from app.schemas.common import SoftDeleteRead, TimestampedRead


class AffiliationBase(BaseModel):
    rit_relationship: str | None = None
    graduation_year: int | None = None
    college: str | None = None
    program: str | None = None
    role: str | None = None


class AffiliationCreate(AffiliationBase):
    person_id: uuid.UUID


class AffiliationRead(TimestampedRead, AffiliationBase):
    person_id: uuid.UUID


class PersonBase(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    title: str | None = None
    notes: str | None = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    title: str | None = None
    notes: str | None = None


class PersonRead(SoftDeleteRead, PersonBase):
    pass
