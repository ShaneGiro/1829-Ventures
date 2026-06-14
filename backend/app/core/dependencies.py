"""FastAPI dependency providers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.models.user import User
from app.services import auth_service

# Reusable annotated alias so routes read `db: DbSession` instead of repeating Depends().
DbSession = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_human_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
    access_token: Annotated[str | None, Cookie(alias=auth_service.SESSION_COOKIE_NAME)] = None,
) -> User:
    bearer_token = auth_service.extract_bearer_token(authorization)
    token = access_token or bearer_token
    if token is None:
        raise AuthenticationError("Authentication is required")

    if bearer_token is not None:
        try:
            await auth_service.authenticate_agent_api_key(db, bearer_token)
        except AuthenticationError:
            pass
        else:
            raise PermissionDeniedError("Agent API keys are only accepted on agent routes")

    return await auth_service.authenticate_jwt(db, token)


async def get_current_agent_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    api_key = auth_service.extract_bearer_token(authorization)
    if api_key is None:
        raise AuthenticationError("Agent API key is required")
    user = await auth_service.authenticate_agent_api_key(db, api_key)
    if not user.is_agent:
        raise PermissionDeniedError("Agent API key is required")
    return user


CurrentUser = Annotated[User, Depends(get_current_human_user)]
CurrentAgent = Annotated[User, Depends(get_current_agent_user)]
