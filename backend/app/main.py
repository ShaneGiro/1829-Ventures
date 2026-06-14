"""FastAPI application factory and wiring.

Maps the typed AppError hierarchy onto HTTP responses so services stay free of
HTTP concerns, installs request-ID + rate-limit middleware, and mounts the API
router under the configured prefix.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.middleware import RateLimitMiddleware, RequestIDMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging(level="DEBUG" if settings.debug else "INFO")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # Middleware (added last runs first on the way in).
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.jwt_secret,
        same_site="lax",
        https_only=not settings.debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
