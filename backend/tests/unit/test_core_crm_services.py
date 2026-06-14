"""Focused tests for Agent 04 core CRM service behavior."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.core.audit import AuditActor
from app.core.constants import ActorType, RelationshipStatus
from app.integrations.storage import PresignedUpload
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.document import Document
from app.models.fund import Fund
from app.models.investment import Investment
from app.models.person import Person
from app.models.user import User
from app.schemas.company_contact import CompanyContactCreate
from app.schemas.document import PresignedUploadRequest
from app.schemas.investment import InvestmentCreate
from app.services import (
    audit_service,
    company_service,
    document_service,
    investment_service,
    people_service,
)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _obj: object) -> None:
        return None


def actor() -> User:
    return User(id=uuid.uuid4(), email="member@g.rit.edu", full_name="Member")


@pytest.mark.asyncio
async def test_company_completeness_tracks_required_v1_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    company = Company(
        id=uuid.uuid4(),
        name="Minimal Co",
        sector="Other",
        relationship_status=RelationshipStatus.IDENTIFIED,
    )
    session = FakeSession()
    monkeypatch.setattr(
        company_service.company_repo,
        "has_primary_contact",
        AsyncMock(return_value=False),
    )
    monkeypatch.setattr(
        company_service.company_repo,
        "count_company_tags",
        AsyncMock(return_value=0),
    )

    completeness = await company_service.refresh_completeness(session, company)

    assert completeness.completeness_pct == 28.57
    assert completeness.missing_fields == [
        "website",
        "description",
        "location",
        "primary_contact",
        "tags",
    ]
    assert company.completeness_pct == 28.57


@pytest.mark.asyncio
async def test_creating_primary_contact_clears_existing_primary_and_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = actor()
    company = Company(id=uuid.uuid4(), name="Contact Co")
    person = Person(id=uuid.uuid4(), full_name="Founder")
    session = FakeSession()
    monkeypatch.setattr(
        people_service.company_service,
        "get_company",
        AsyncMock(return_value=company),
    )
    monkeypatch.setattr(people_service, "get_person", AsyncMock(return_value=person))
    monkeypatch.setattr(
        people_service.people_repo,
        "get_contact_by_pair",
        AsyncMock(return_value=None),
    )
    clear_primary = AsyncMock()
    monkeypatch.setattr(people_service.people_repo, "clear_primary_contacts", clear_primary)
    monkeypatch.setattr(
        people_service.people_repo,
        "create_contact",
        AsyncMock(side_effect=lambda _session, contact: contact),
    )
    monkeypatch.setattr(people_service.company_service, "refresh_completeness", AsyncMock())
    audit_create = AsyncMock()
    monkeypatch.setattr(people_service.audit_service, "record_create", audit_create)

    contact = await people_service.create_company_contact(
        session,
        CompanyContactCreate(company_id=company.id, person_id=person.id, is_primary=True),
        user,
    )

    assert isinstance(contact, CompanyContact)
    assert contact.is_primary is True
    clear_primary.assert_awaited_once_with(session, company.id)
    audit_create.assert_awaited_once()
    assert session.committed is True


@pytest.mark.asyncio
async def test_investment_create_validates_fund_and_company_then_audits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = actor()
    fund = Fund(id=uuid.uuid4(), name="Fund I")
    company = Company(id=uuid.uuid4(), name="Portfolio Co")
    session = FakeSession()
    monkeypatch.setattr(investment_service, "get_fund", AsyncMock(return_value=fund))
    monkeypatch.setattr(
        investment_service.company_repo,
        "get_company",
        AsyncMock(return_value=company),
    )
    monkeypatch.setattr(
        investment_service.investment_repo,
        "create_investment",
        AsyncMock(side_effect=lambda _session, investment: investment),
    )
    audit_create = AsyncMock()
    monkeypatch.setattr(investment_service.audit_service, "record_create", audit_create)

    investment = await investment_service.create_investment(
        session,
        InvestmentCreate(fund_id=fund.id, company_id=company.id, amount=Decimal("100000")),
        user,
    )

    assert isinstance(investment, Investment)
    assert investment.amount == Decimal("100000")
    audit_create.assert_awaited_once()
    assert session.committed is True


@pytest.mark.asyncio
async def test_presigned_upload_creates_document_metadata_and_storage_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = actor()
    session = FakeSession()

    async def create_document(_session: FakeSession, document: Document) -> Document:
        document.id = uuid.uuid4()
        return document

    monkeypatch.setattr(
        document_service.document_repo,
        "create_document",
        create_document,
    )
    audit_create = AsyncMock()
    monkeypatch.setattr(document_service.audit_service, "record_create", audit_create)

    class FakeStorage:
        def create_presigned_upload(
            self,
            *,
            storage_key: str,
            content_type: str | None,
            expires_in: int = 3600,
        ) -> PresignedUpload:
            assert content_type == "application/pdf"
            assert expires_in == 3600
            return PresignedUpload(
                upload_url=f"https://minio.test/{storage_key}",
                storage_key=storage_key,
            )

    document, upload_url = await document_service.create_presigned_upload(
        session,
        PresignedUploadRequest(filename="pitch/deck.pdf", content_type="application/pdf"),
        user,
        storage=FakeStorage(),
    )

    assert document.storage_key == f"documents/{document.id}/pitch_deck.pdf"
    assert upload_url == f"https://minio.test/{document.storage_key}"
    audit_create.assert_awaited_once()
    assert session.committed is True


@pytest.mark.asyncio
async def test_audit_update_writes_one_row_per_changed_field() -> None:
    session = FakeSession()
    audit_actor = AuditActor(
        actor_type=ActorType.HUMAN,
        actor_id=uuid.uuid4(),
        actor_label="Member",
    )
    company = Company(id=uuid.uuid4(), name="Audit Co")

    logs = await audit_service.record_update(
        session,
        actor=audit_actor,
        entity=company,
        changes={
            "name": ("Old", "New"),
            "updated_at": (datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 2, tzinfo=UTC)),
        },
    )

    assert len(logs) == 2
    assert all(isinstance(log, AuditLog) for log in logs)
    assert logs[0].old_value == {"name": "Old"}
    assert logs[1].new_value == {"updated_at": "2026-01-02T00:00:00+00:00"}
