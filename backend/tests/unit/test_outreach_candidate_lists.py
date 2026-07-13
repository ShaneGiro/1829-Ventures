"""Saved outreach-candidate list service and API tests."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.core.constants import (
    OutreachCandidateListStatus,
    OutreachCandidateStatus,
    Role,
)
from app.core.database import get_async_session
from app.core.dependencies import get_current_human_user
from app.main import app
from app.models.outreach_candidate_list import (
    OutreachCandidateList,
    OutreachCandidateListItem,
)
from app.models.user import User
from app.schemas.outreach_candidate import (
    OutreachCandidateListCreate,
    OutreachCandidateListItemUpdate,
)
from app.services import outreach_candidate_list_service


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


def _user(email: str = "member@g.rit.edu") -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        full_name="RIT Member",
        role=Role.MEMBER,
        is_active=True,
        is_agent=False,
    )


@pytest.mark.asyncio
async def test_create_candidate_list_persists_filter_and_owner_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = _user("creator@g.rit.edu")
    owner = _user("owner@g.rit.edu")
    session = FakeSession()

    async def create_list(
        _session: FakeSession, candidate_list: OutreachCandidateList
    ) -> OutreachCandidateList:
        candidate_list.id = uuid.uuid4()
        return candidate_list

    monkeypatch.setattr(
        outreach_candidate_list_service.user_repo,
        "get_user_by_id",
        AsyncMock(return_value=owner),
    )
    monkeypatch.setattr(outreach_candidate_list_service.list_repo, "create_list", create_list)
    audit_create = AsyncMock()
    monkeypatch.setattr(
        outreach_candidate_list_service.audit_service, "record_create", audit_create
    )

    candidate_list = await outreach_candidate_list_service.create_candidate_list(
        session,
        OutreachCandidateListCreate(
            name="  RIT alumni founders  ",
            owner_id=owner.id,
            default_filters={"include_recently_contacted": False},
        ),
        actor,
    )

    assert candidate_list.name == "RIT alumni founders"
    assert candidate_list.owner_id == owner.id
    assert candidate_list.default_filters == {"include_recently_contacted": False}
    assert [entry["field"] for entry in candidate_list.change_history] == [
        "status",
        "owner_id",
    ]
    assert candidate_list.change_history[-1]["changed_by_label"] == "RIT Member"
    audit_create.assert_awaited_once()
    assert session.committed is True


@pytest.mark.asyncio
async def test_item_update_appends_assignment_and_status_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = _user("creator@g.rit.edu")
    owner = _user("owner@g.rit.edu")
    list_id = uuid.uuid4()
    item_id = uuid.uuid4()
    candidate_list = OutreachCandidateList(
        id=list_id,
        name="Candidates",
        status=OutreachCandidateListStatus.ACTIVE,
    )
    item = OutreachCandidateListItem(
        id=item_id,
        list_id=list_id,
        company_id=uuid.uuid4(),
        candidate_status=OutreachCandidateStatus.NEW,
        change_history=[{"field": "candidate_status", "to": "new"}],
    )
    session = FakeSession()

    monkeypatch.setattr(
        outreach_candidate_list_service,
        "get_candidate_list",
        AsyncMock(return_value=candidate_list),
    )
    monkeypatch.setattr(
        outreach_candidate_list_service.list_repo,
        "get_item",
        AsyncMock(return_value=item),
    )
    monkeypatch.setattr(
        outreach_candidate_list_service.user_repo,
        "get_user_by_id",
        AsyncMock(return_value=owner),
    )
    audit_update = AsyncMock()
    monkeypatch.setattr(
        outreach_candidate_list_service.audit_service, "record_update", audit_update
    )

    updated = await outreach_candidate_list_service.update_candidate_list_item(
        session,
        list_id,
        item_id,
        OutreachCandidateListItemUpdate(
            assigned_to_id=owner.id,
            candidate_status=OutreachCandidateStatus.READY_TO_CONTACT,
            change_reason="Founder profile verified",
        ),
        actor,
    )

    assert updated.assigned_to_id == owner.id
    assert updated.candidate_status == OutreachCandidateStatus.READY_TO_CONTACT
    assert [entry["field"] for entry in updated.change_history] == [
        "candidate_status",
        "assigned_to_id",
        "candidate_status",
    ]
    assert updated.change_history[-1]["reason"] == "Founder profile verified"
    audit_update.assert_awaited_once()
    assert session.committed is True


@pytest.mark.asyncio
async def test_saved_list_api_creates_list_and_updates_item(
    client: AsyncClient,
    api_prefix: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = _user()
    now = datetime.now(UTC)
    list_id = uuid.uuid4()
    item_id = uuid.uuid4()
    company_id = uuid.uuid4()
    candidate_list = OutreachCandidateList(
        id=list_id,
        name="Deep tech targets",
        status=OutreachCandidateListStatus.ACTIVE,
        default_filters={"stage": ["Seed"]},
        created_by_id=actor.id,
        change_history=[],
        created_at=now,
        updated_at=now,
    )
    item = OutreachCandidateListItem(
        id=item_id,
        list_id=list_id,
        company_id=company_id,
        assigned_to_id=actor.id,
        candidate_status=OutreachCandidateStatus.CONTACTED,
        rank_reasons=[],
        score_breakdown={},
        change_history=[{"field": "candidate_status", "from": "new", "to": "contacted"}],
        created_at=now,
        updated_at=now,
    )

    async def override_user() -> User:
        return actor

    async def override_session() -> AsyncIterator[object]:
        yield object()

    async def fake_create(
        _session: object, payload: OutreachCandidateListCreate, _actor: User
    ) -> OutreachCandidateList:
        assert payload.default_filters == {"stage": ["Seed"]}
        return candidate_list

    async def fake_update_item(
        _session: object,
        requested_list_id: uuid.UUID,
        requested_item_id: uuid.UUID,
        payload: OutreachCandidateListItemUpdate,
        _actor: User,
    ) -> OutreachCandidateListItem:
        assert requested_list_id == list_id
        assert requested_item_id == item_id
        assert payload.candidate_status == OutreachCandidateStatus.CONTACTED
        return item

    app.dependency_overrides[get_current_human_user] = override_user
    app.dependency_overrides[get_async_session] = override_session
    monkeypatch.setattr(outreach_candidate_list_service, "create_candidate_list", fake_create)
    monkeypatch.setattr(
        outreach_candidate_list_service, "update_candidate_list_item", fake_update_item
    )
    try:
        create_response = await client.post(
            f"{api_prefix}/outreach-candidates/lists",
            json={
                "name": "Deep tech targets",
                "default_filters": {"stage": ["Seed"]},
            },
        )
        update_response = await client.patch(
            f"{api_prefix}/outreach-candidates/lists/{list_id}/items/{item_id}",
            json={
                "assigned_to_id": str(actor.id),
                "candidate_status": "contacted",
                "change_reason": "Sent introduction",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert create_response.status_code == 201
    assert create_response.json()["id"] == str(list_id)
    assert create_response.json()["default_filters"] == {"stage": ["Seed"]}
    assert update_response.status_code == 200
    assert update_response.json()["candidate_status"] == "contacted"
    assert update_response.json()["assigned_to_id"] == str(actor.id)
