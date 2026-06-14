"""Request-ID injection and Redis token-bucket rate limiting.

No external rate-limit library — Redis is already in the stack, so a small
token-bucket keyed by actor + endpoint tier is enough. Limits are enforced per
tool/endpoint tier; Agent 10 maps Ritchie's agent surfaces onto these tiers
(reads 120/min, authorized writes 60/min).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import request_id_ctx

REQUEST_ID_HEADER = "X-Request-ID"

# Endpoint tier -> (max tokens, refill window seconds).
RATE_LIMIT_TIERS: dict[str, tuple[int, int]] = {
    "agent_read": (120, 60),
    "agent_write": (60, 60),
    "default": (300, 60),
}


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to the log context and echo it in the response header."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis token-bucket rate limiter.

    Skeleton wiring for Agent 01: limits the `default` tier per client. Agent 10
    classifies agent endpoints into the agent_read/agent_write tiers. Fails open
    if Redis is unavailable — rate limiting must never take down the API.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._redis: aioredis.Redis | None = None

    @property
    def redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    @staticmethod
    def _tier_for(request: Request) -> str:
        # Agent 10 refines this; for now everything is the default tier.
        if request.url.path.startswith(f"{settings.api_v1_prefix}/agent"):
            return "agent_read"
        return "default"

    @staticmethod
    def _client_key(request: Request) -> str:
        actor = request.headers.get("X-API-Key") or (
            request.client.host if request.client else "anonymous"
        )
        return actor

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        tier = self._tier_for(request)
        max_tokens, window = RATE_LIMIT_TIERS[tier]
        bucket_key = f"ratelimit:{tier}:{self._client_key(request)}:{int(time.time() // window)}"

        try:
            current = await self.redis.incr(bucket_key)
            if current == 1:
                await self.redis.expire(bucket_key, window)
            if current > max_tokens:
                return JSONResponse(
                    status_code=429,
                    content={"code": "rate_limited", "message": "Rate limit exceeded"},
                )
        except Exception:  # noqa: BLE001 - fail open; never block on limiter errors
            pass

        return await call_next(request)
