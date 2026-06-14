"""Human/system audit-log service."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditActor
from app.models.audit_log import AuditLog
from app.models.base import Base


def _jsonable(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value


def snapshot_model(model: Base, *, exclude: set[str] | None = None) -> dict[str, Any]:
    excluded = exclude or set()
    return {
        column.name: _jsonable(getattr(model, column.name))
        for column in model.__table__.columns
        if column.name not in excluded
    }


async def record_create(
    session: AsyncSession,
    *,
    actor: AuditActor,
    entity: Base,
    reason: str | None = None,
) -> AuditLog:
    audit = AuditLog(
        actor_type=actor.actor_type,
        actor_id=actor.actor_id,
        actor_label=actor.actor_label,
        action="create",
        entity_type=entity.__tablename__,
        entity_id=getattr(entity, "id", None),
        field_name=None,
        old_value=None,
        new_value=snapshot_model(entity),
        reason=reason,
    )
    session.add(audit)
    await session.flush()
    return audit


async def record_update(
    session: AsyncSession,
    *,
    actor: AuditActor,
    entity: Base,
    changes: dict[str, tuple[Any, Any]],
    reason: str | None = None,
) -> list[AuditLog]:
    logs: list[AuditLog] = []
    for field_name, (old_value, new_value) in changes.items():
        audit = AuditLog(
            actor_type=actor.actor_type,
            actor_id=actor.actor_id,
            actor_label=actor.actor_label,
            action="update",
            entity_type=entity.__tablename__,
            entity_id=getattr(entity, "id", None),
            field_name=field_name,
            old_value={field_name: _jsonable(old_value)},
            new_value={field_name: _jsonable(new_value)},
            reason=reason,
        )
        session.add(audit)
        logs.append(audit)
    if logs:
        await session.flush()
    return logs


async def record_archive(
    session: AsyncSession,
    *,
    actor: AuditActor,
    entity: Base,
    old_snapshot: dict[str, Any],
    reason: str | None = None,
) -> AuditLog:
    audit = AuditLog(
        actor_type=actor.actor_type,
        actor_id=actor.actor_id,
        actor_label=actor.actor_label,
        action="archive",
        entity_type=entity.__tablename__,
        entity_id=getattr(entity, "id", None),
        field_name="archived_at",
        old_value=old_snapshot,
        new_value=snapshot_model(entity),
        reason=reason,
    )
    session.add(audit)
    await session.flush()
    return audit
