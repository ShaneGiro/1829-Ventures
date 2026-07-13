"""Organization/legal-entity foundation tests."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.constants import LegalEntityRelationshipType, LegalEntityType, Role
from app.core.exceptions import ConflictError, PermissionDeniedError, ValidationError
from app.models.legal_entity import LegalEntity
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.schemas.legal_entity import LegalEntityRelationshipCreate
from app.services import organization_service


def make_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="director@rit.edu",
        role=Role.MANAGING_DIRECTOR,
        is_active=True,
        is_agent=False,
    )


def test_relationship_schema_rejects_self_reference() -> None:
    entity_id = uuid.uuid4()
    with pytest.raises(PydanticValidationError):
        LegalEntityRelationshipCreate(
            parent_entity_id=entity_id,
            child_entity_id=entity_id,
            relationship_type=LegalEntityRelationshipType.OWNS,
            effective_from=date(2026, 1, 1),
        )


def test_relationship_schema_rejects_invalid_effective_dates() -> None:
    with pytest.raises(PydanticValidationError):
        LegalEntityRelationshipCreate(
            parent_entity_id=uuid.uuid4(),
            child_entity_id=uuid.uuid4(),
            relationship_type=LegalEntityRelationshipType.MANAGES,
            effective_from=date(2026, 2, 1),
            effective_to=date(2026, 1, 1),
        )


@pytest.mark.asyncio
async def test_require_membership_rejects_out_of_scope_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        organization_service.organization_repo,
        "get_membership",
        AsyncMock(return_value=None),
    )
    with pytest.raises(PermissionDeniedError, match="does not have access"):
        await organization_service.require_membership(
            AsyncMock(), uuid.uuid4(), make_user()
        )


@pytest.mark.asyncio
async def test_relationship_requires_same_organization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = LegalEntity(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        legal_name="RIT GP",
        entity_type=LegalEntityType.GENERAL_PARTNER,
    )
    child = LegalEntity(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        legal_name="Fund I",
        entity_type=LegalEntityType.FUND,
    )
    monkeypatch.setattr(
        organization_service,
        "get_legal_entity",
        AsyncMock(side_effect=[parent, child]),
    )
    payload = LegalEntityRelationshipCreate(
        parent_entity_id=parent.id,
        child_entity_id=child.id,
        relationship_type=LegalEntityRelationshipType.GENERAL_PARTNER_OF,
        effective_from=date(2026, 1, 1),
    )
    with pytest.raises(ValidationError, match="same organization"):
        await organization_service.create_relationship(AsyncMock(), payload, make_user())


@pytest.mark.asyncio
async def test_relationship_rejects_cycle(monkeypatch: pytest.MonkeyPatch) -> None:
    organization_id = uuid.uuid4()
    parent = LegalEntity(
        id=uuid.uuid4(),
        organization_id=organization_id,
        legal_name="RIT GP",
        entity_type=LegalEntityType.GENERAL_PARTNER,
    )
    child = LegalEntity(
        id=uuid.uuid4(),
        organization_id=organization_id,
        legal_name="Fund I",
        entity_type=LegalEntityType.FUND,
    )
    monkeypatch.setattr(
        organization_service,
        "get_legal_entity",
        AsyncMock(side_effect=[parent, child]),
    )
    monkeypatch.setattr(
        organization_service.organization_repo,
        "relationship_would_create_cycle",
        AsyncMock(return_value=True),
    )
    payload = LegalEntityRelationshipCreate(
        parent_entity_id=parent.id,
        child_entity_id=child.id,
        relationship_type=LegalEntityRelationshipType.GENERAL_PARTNER_OF,
        effective_from=date(2026, 1, 1),
    )
    with pytest.raises(ConflictError, match="create a cycle"):
        await organization_service.create_relationship(AsyncMock(), payload, make_user())


def test_organization_relationship_models_are_wired() -> None:
    assert "memberships" in Organization.__mapper__.relationships
    assert "organization" in OrganizationMembership.__mapper__.relationships
