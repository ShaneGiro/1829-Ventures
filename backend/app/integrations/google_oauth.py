"""Google OAuth integration wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.exceptions import AuthenticationError


@dataclass(frozen=True)
class GoogleProfile:
    """Normalized Google identity profile used by auth services."""

    email: str
    full_name: str | None = None
    avatar_url: str | None = None


class GoogleOAuthClient:
    """Small Authlib wrapper so route code stays HTTP-only."""

    def __init__(self) -> None:
        self._oauth = OAuth()
        self._oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile",
            },
        )

    async def authorize_redirect(self, request: Request) -> Response:
        if not settings.google_client_id or not settings.google_client_secret:
            raise AuthenticationError("Google OAuth is not configured")
        google = self._oauth.create_client("google")
        if google is None:
            raise AuthenticationError("Google OAuth client is unavailable")
        return cast(
            "Response",
            await google.authorize_redirect(request, settings.google_redirect_uri),
        )

    async def fetch_profile(self, request: Request) -> GoogleProfile:
        google = self._oauth.create_client("google")
        if google is None:
            raise AuthenticationError("Google OAuth client is unavailable")

        token = await google.authorize_access_token(request)
        profile: dict[str, Any] | None = token.get("userinfo")
        if profile is None:
            profile = await google.userinfo(token=token)

        email = profile.get("email")
        if not isinstance(email, str) or not email:
            raise AuthenticationError("Google profile did not include an email address")

        full_name = profile.get("name")
        avatar_url = profile.get("picture")
        return GoogleProfile(
            email=email,
            full_name=full_name if isinstance(full_name, str) else None,
            avatar_url=avatar_url if isinstance(avatar_url, str) else None,
        )


google_oauth_client = GoogleOAuthClient()
