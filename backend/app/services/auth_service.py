"""Authentication service: OAuth callbacks, JWT sessions, and agent API keys."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import Role
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import create_access_token, decode_access_token, hash_api_key, verify_api_key
from app.integrations.google_oauth import GoogleProfile
from app.models.user import User
from app.repositories import users as user_repo

SESSION_COOKIE_NAME = "access_token"
AUTH_COOKIE_MAX_AGE_SECONDS = settings.jwt_expire_minutes * 60
BEARER_PREFIX = "Bearer "
AGENT_EMAIL = "ritchie-agent@1829.ventures"


@dataclass(frozen=True)
class AuthResult:
    user: User
    access_token: str


def is_allowed_email(email: str) -> bool:
    normalized = email.strip().lower()
    return any(
        normalized == domain or normalized.endswith(f"@{domain}")
        for domain in settings.allowed_domains_list
    )


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith(BEARER_PREFIX):
        return None
    token = authorization.removeprefix(BEARER_PREFIX).strip()
    return token or None


def is_configured_agent_api_key(api_key: str) -> bool:
    return bool(settings.agent_api_key) and verify_api_key(
        api_key, hash_api_key(settings.agent_api_key)
    )


def build_ephemeral_agent_user() -> User:
    return User(
        id=uuid.uuid4(),
        email=AGENT_EMAIL,
        full_name="Ritchie",
        role=Role.AGENT,
        is_agent=True,
        is_active=True,
        api_key_hash=hash_api_key(settings.agent_api_key) if settings.agent_api_key else None,
    )


async def authenticate_oauth_profile(
    session: AsyncSession,
    profile: GoogleProfile,
) -> AuthResult:
    if not is_allowed_email(profile.email):
        raise PermissionDeniedError("Google account domain is not eligible for this CRM")

    user = await user_repo.upsert_human_user(
        session,
        email=profile.email,
        full_name=profile.full_name,
        avatar_url=profile.avatar_url,
    )
    await session.commit()
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": str(user.role), "actor": "human"},
    )
    return AuthResult(user=user, access_token=access_token)


async def authenticate_jwt(session: AsyncSession, token: str) -> User:
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise AuthenticationError("Token is missing a subject")
    try:
        user_id = uuid.UUID(subject)
    except ValueError as exc:
        raise AuthenticationError("Token subject is invalid") from exc

    user = await user_repo.get_user_by_id(session, user_id)
    if user is None or user.is_agent or not user.is_active:
        raise AuthenticationError("User is not active or does not exist")
    return user


async def authenticate_agent_api_key(session: AsyncSession, api_key: str) -> User:
    if not api_key:
        raise AuthenticationError("Agent API key is required")

    key_hash = hash_api_key(api_key)
    user = await user_repo.get_agent_by_api_key_hash(session, key_hash)
    if user is not None:
        return user

    if is_configured_agent_api_key(api_key):
        return build_ephemeral_agent_user()

    raise AuthenticationError("Invalid agent API key")


def create_session_token(user: User) -> str:
    return create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email, "role": str(user.role), "actor": "human"},
    )
