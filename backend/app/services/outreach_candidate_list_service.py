"""Business rules for durable outreach-candidate lists."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.constants import OutreachCandidateListStatus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.outreach_candidate_list import (
    OutreachCandidateList,
    OutreachCandidateListItem,
)
from app.models.user import User
from app.repositories import companies as company_repo
from app.repositories import outreach_candidate_lists as list_repo
from app.repositories import people as people_repo
from app.repositories import users as user_repo
from app.schemas.outreach_candidate import (
    OutreachCandidateListCreate,
    OutreachCandidateListItemCreate,
    OutreachCandidateListItemUpdate,
    OutreachCandidateListUpdate,
)
from app.services import audit_service


def _history_value(value: object) -> object:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value


def _change_entry(
    *,
    actor: User,
    field: str,
    old_value: object,
    new_value: object,
    reason: str | None,
) -> dict[str, Any]:
    return {
        "changed_at": datetime.now(UTC).isoformat(),
        "changed_by_id": str(actor.id),
        "changed_by_label": actor.full_name or actor.email,
        "field": field,
        "from": _history_value(old_value),
        "to": _history_value(new_value),
        "reason": reason,
    }


async def _validate_owner(session: AsyncSession, owner_id: uuid.UUID | None) -> User | None:
    if owner_id is None:
        return None
    owner = await user_repo.get_user_by_id(session, owner_id)
    if owner is None or not owner.is_active:
        raise ValidationError("Candidate owner does not exist or is inactive")
    return owner


async def get_candidate_list(
    session: AsyncSession,
    list_id: uuid.UUID,
    *,
    include_archived: bool = False,
    with_items: bool = True,
) -> OutreachCandidateList:
    candidate_list = await list_repo.get_list(
        session,
        list_id,
        include_archived=include_archived,
        with_items=with_items,
    )
    if candidate_list is None:
        raise NotFoundError("Outreach candidate list not found")
    return candidate_list


async def list_candidate_lists(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    include_archived: bool = False,
) -> tuple[list[OutreachCandidateList], int]:
    lists = await list_repo.list_lists(
        session,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )
    total = await list_repo.count_lists(session, include_archived=include_archived)
    return lists, total


async def create_candidate_list(
    session: AsyncSession, payload: OutreachCandidateListCreate, actor: User
) -> OutreachCandidateList:
    await _validate_owner(session, payload.owner_id)
    candidate_list = OutreachCandidateList(
        name=payload.name.strip(),
        description=payload.description,
        owner_id=payload.owner_id,
        created_by_id=actor.id,
        status=OutreachCandidateListStatus.ACTIVE,
        default_filters=payload.default_filters,
    )
    history = [
        _change_entry(
            actor=actor,
            field="status",
            old_value=None,
            new_value=OutreachCandidateListStatus.ACTIVE,
            reason="candidate_list_created",
        )
    ]
    if payload.owner_id is not None:
        history.append(
            _change_entry(
                actor=actor,
                field="owner_id",
                old_value=None,
                new_value=payload.owner_id,
                reason="candidate_list_created",
            )
        )
    candidate_list.change_history = history
    await list_repo.create_list(session, candidate_list)
    await audit_service.record_create(
        session,
        actor=actor_from_user(actor),
        entity=candidate_list,
        reason="outreach_candidate_list_created",
    )
    await session.commit()
    await session.refresh(candidate_list)
    return candidate_list


async def update_candidate_list(
    session: AsyncSession,
    list_id: uuid.UUID,
    payload: OutreachCandidateListUpdate,
    actor: User,
) -> OutreachCandidateList:
    candidate_list = await get_candidate_list(
        session, list_id, include_archived=True, with_items=False
    )
    updates = payload.model_dump(exclude_unset=True, exclude={"change_reason"})
    if updates.get("name") is None and "name" in updates:
        raise ValidationError("Candidate list name cannot be null")
    if "owner_id" in updates:
        await _validate_owner(session, updates["owner_id"])

    changes: dict[str, tuple[object, object]] = {}
    history = list(candidate_list.change_history or [])
    for field, value in updates.items():
        if field == "name":
            value = value.strip()
        old_value = getattr(candidate_list, field)
        if old_value == value:
            continue
        changes[field] = (old_value, value)
        setattr(candidate_list, field, value)
        if field in {"owner_id", "status"}:
            history.append(
                _change_entry(
                    actor=actor,
                    field=field,
                    old_value=old_value,
                    new_value=value,
                    reason=payload.change_reason,
                )
            )
    if changes:
        candidate_list.change_history = history
        await audit_service.record_update(
            session,
            actor=actor_from_user(actor),
            entity=candidate_list,
            changes=changes,
            reason=payload.change_reason or "outreach_candidate_list_updated",
        )
    await session.commit()
    await session.refresh(candidate_list)
    return candidate_list


async def add_candidate_list_item(
    session: AsyncSession,
    list_id: uuid.UUID,
    payload: OutreachCandidateListItemCreate,
    actor: User,
) -> OutreachCandidateListItem:
    candidate_list = await get_candidate_list(session, list_id, with_items=False)
    if candidate_list.status != OutreachCandidateListStatus.ACTIVE:
        raise ValidationError("Items can only be added to an active candidate list")
    if await company_repo.get_company(session, payload.company_id) is None:
        raise ValidationError("Candidate company does not exist")
    if (
        payload.person_id is not None
        and await people_repo.get_person(session, payload.person_id) is None
    ):
        raise ValidationError("Candidate person does not exist")
    await _validate_owner(session, payload.assigned_to_id)
    if await list_repo.get_item_by_company(
        session, list_id=list_id, company_id=payload.company_id
    ) is not None:
        raise ConflictError("Company is already in this candidate list")

    item = OutreachCandidateListItem(
        list_id=list_id,
        company_id=payload.company_id,
        person_id=payload.person_id,
        assigned_to_id=payload.assigned_to_id,
        candidate_status=payload.candidate_status,
        rank_score=payload.rank_score,
        rank_reasons=payload.rank_reasons,
        score_version=payload.score_version,
        score_breakdown=payload.score_breakdown,
        why_this_company=payload.why_this_company,
    )
    history = [
        _change_entry(
            actor=actor,
            field="candidate_status",
            old_value=None,
            new_value=payload.candidate_status,
            reason=payload.change_reason or "candidate_added",
        )
    ]
    if payload.assigned_to_id is not None:
        history.append(
            _change_entry(
                actor=actor,
                field="assigned_to_id",
                old_value=None,
                new_value=payload.assigned_to_id,
                reason=payload.change_reason or "candidate_added",
            )
        )
    item.change_history = history
    await list_repo.create_item(session, item)
    await audit_service.record_create(
        session,
        actor=actor_from_user(actor),
        entity=item,
        reason=payload.change_reason or "outreach_candidate_added",
    )
    await session.commit()
    await session.refresh(item)
    return item


async def update_candidate_list_item(
    session: AsyncSession,
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: OutreachCandidateListItemUpdate,
    actor: User,
) -> OutreachCandidateListItem:
    candidate_list = await get_candidate_list(session, list_id, with_items=False)
    if candidate_list.status == OutreachCandidateListStatus.ARCHIVED:
        raise ValidationError("Archived candidate lists are read-only")
    item = await list_repo.get_item(session, list_id=list_id, item_id=item_id)
    if item is None:
        raise NotFoundError("Outreach candidate list item not found")

    updates = payload.model_dump(exclude_unset=True, exclude={"change_reason"})
    if "assigned_to_id" in updates:
        await _validate_owner(session, updates["assigned_to_id"])
    changes: dict[str, tuple[object, object]] = {}
    history = list(item.change_history or [])
    for field, value in updates.items():
        old_value = getattr(item, field)
        if old_value == value:
            continue
        changes[field] = (old_value, value)
        setattr(item, field, value)
        history.append(
            _change_entry(
                actor=actor,
                field=field,
                old_value=old_value,
                new_value=value,
                reason=payload.change_reason,
            )
        )
    if changes:
        item.change_history = history
        await audit_service.record_update(
            session,
            actor=actor_from_user(actor),
            entity=item,
            changes=changes,
            reason=payload.change_reason or "outreach_candidate_item_updated",
        )
    await session.commit()
    await session.refresh(item)
    return item
