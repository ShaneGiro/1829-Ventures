"""Single include point for all API route modules.

Agent 01 wires health only. Subsequent agents register their routers here:
auth, users, companies, people, deals, etc. Keep this the one place sub-routers
are mounted so the wiring is auditable.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    auth,
    companies,
    deal_statuses,
    deals,
    documents,
    health,
    imports,
    interactions,
    investments,
    people,
    portfolio_metrics,
    tasks,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(people.contacts_router, prefix="/company-contacts", tags=["people"])
api_router.include_router(people.affiliations_router, prefix="/affiliations", tags=["people"])
api_router.include_router(interactions.router, prefix="/interactions", tags=["interactions"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(deal_statuses.router, prefix="/deal-statuses", tags=["deal-statuses"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(investments.funds_router, prefix="/funds", tags=["funds"])
api_router.include_router(investments.router, prefix="/investments", tags=["investments"])
api_router.include_router(
    portfolio_metrics.router,
    prefix="/portfolio-metrics",
    tags=["portfolio_metrics"],
)
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
