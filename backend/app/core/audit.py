"""Audit helpers shared by services.

Routes pass the authenticated user into services; services turn that into this
small serializable actor context before writing audit rows.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.core.constants import ActorType
from app.models.user import User


@dataclass(frozen=True)
class AuditActor:
    actor_type: ActorType
    actor_id: uuid.UUID | None
    actor_label: str | None


def actor_from_user(user: User) -> AuditActor:
    actor_type = ActorType.AGENT if user.is_agent else ActorType.HUMAN
    return AuditActor(
        actor_type=actor_type,
        actor_id=user.id,
        actor_label=user.full_name or user.email,
    )


def system_actor(label: str = "system") -> AuditActor:
    return AuditActor(actor_type=ActorType.SYSTEM, actor_id=None, actor_label=label)
