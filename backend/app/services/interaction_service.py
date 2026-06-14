"""Interaction service: notes, calls, meetings, emails, and timelines."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.exceptions import NotFoundError, ValidationError
from app.models.interaction import Interaction
from app.models.user import User
from app.repositories import interactions as interaction_repo
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.services import audit_service


async def get_interaction(
    session: AsyncSession, interaction_id: uuid.UUID, *, include_archived: bool = False
) -> Interaction:
    interaction = await interaction_repo.get_interaction(
        session, interaction_id, include_archived=include_archived
    )
    if interaction is None:
        raise NotFoundError("Interaction not found")
    return interaction


async def create_interaction(
    session: AsyncSession, payload: InteractionCreate, actor: User
) -> Interaction:
    interaction = Interaction(**payload.model_dump(exclude_none=True))
    await interaction_repo.create_interaction(session, interaction)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=interaction)
    await session.commit()
    await session.refresh(interaction)
    return interaction


async def update_interaction(
    session: AsyncSession,
    interaction_id: uuid.UUID,
    payload: InteractionUpdate,
    actor: User,
) -> Interaction:
    interaction = await get_interaction(session, interaction_id)
    updates = payload.model_dump(exclude_unset=True)
    if "interaction_type" in updates and updates["interaction_type"] is None:
        raise ValidationError("interaction_type cannot be null")
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(interaction, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(interaction, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=interaction, changes=changes
        )
    await session.commit()
    await session.refresh(interaction)
    return interaction


async def archive_interaction(
    session: AsyncSession, interaction_id: uuid.UUID, actor: User
) -> Interaction:
    interaction = await get_interaction(session, interaction_id)
    old_snapshot = audit_service.snapshot_model(interaction)
    interaction.archived_at = datetime.now(UTC)
    await audit_service.record_archive(
        session,
        actor=actor_from_user(actor),
        entity=interaction,
        old_snapshot=old_snapshot,
    )
    await session.commit()
    await session.refresh(interaction)
    return interaction
