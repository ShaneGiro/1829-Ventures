"""Single include point for all API route modules.

Agent 01 wires health only. Subsequent agents register their routers here:
auth, users, companies, people, deals, etc. Keep this the one place sub-routers
are mounted so the wiring is auditable.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
