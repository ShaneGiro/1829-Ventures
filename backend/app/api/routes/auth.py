"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from starlette.responses import RedirectResponse

from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession
from app.integrations.google_oauth import google_oauth_client
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter()


@router.get("/login")
async def login(request: Request) -> Response:
    return await google_oauth_client.authorize_redirect(request)


@router.get("/callback")
async def callback(request: Request, db: DbSession) -> RedirectResponse:
    profile = await google_oauth_client.fetch_profile(request)
    result = await auth_service.authenticate_oauth_profile(db, profile)
    response = RedirectResponse(url=settings.frontend_url)
    response.set_cookie(
        auth_service.SESSION_COOKIE_NAME,
        result.access_token,
        max_age=auth_service.AUTH_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    return response


@router.post("/refresh")
async def refresh(
    current_user: CurrentUser, request: Request, response: Response
) -> dict[str, str]:
    token = auth_service.create_session_token(current_user)
    response.set_cookie(
        auth_service.SESSION_COOKIE_NAME,
        token,
        max_age=auth_service.AUTH_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    return {"status": "ok"}


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(auth_service.SESSION_COOKIE_NAME)
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
