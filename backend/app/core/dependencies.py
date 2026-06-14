"""FastAPI dependency providers.

Agent 01 wires the database-session dependency only. Auth/current-user and
permission dependencies are added by Agent 03 (Auth, Users, Permissions).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

# Reusable annotated alias so routes read `db: DbSession` instead of repeating Depends().
DbSession = Annotated[AsyncSession, Depends(get_async_session)]
