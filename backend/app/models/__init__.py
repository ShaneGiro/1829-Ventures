"""SQLAlchemy model registry.

Alembic imports this module to discover metadata for autogenerate. Agent 02 adds
the concrete model imports here so every table is registered. Agent 01 ships only
the declarative Base.
"""

from __future__ import annotations

from app.models.base import Base

__all__ = ["Base"]

# Agent 02 appends model imports below so Base.metadata sees every table, e.g.:
#   from app.models.user import User
#   from app.models.company import Company
