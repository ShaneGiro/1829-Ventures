"""SQLAlchemy model registry.

Alembic imports this module to discover metadata for autogenerate, so every model
must be imported here for its table to be registered on Base.metadata.
"""

from __future__ import annotations

from app.models.affiliation import Affiliation
from app.models.agent_event_log import AgentEventLog
from app.models.agent_policy import AgentPolicy
from app.models.ai_audit_log import AiAuditLog
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.deal import Deal
from app.models.deal_status import DealStatus
from app.models.diligence_checklist_item import DiligenceChecklistItem
from app.models.document import Document
from app.models.fund import Fund
from app.models.import_batch import ImportBatch
from app.models.import_row import ImportRow
from app.models.interaction import Interaction
from app.models.investment import Investment
from app.models.notification import Notification
from app.models.person import Person
from app.models.portfolio_metric import PortfolioMetric
from app.models.rubric import Rubric
from app.models.tag import Tag, company_tags
from app.models.task import Task
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Company",
    "Person",
    "Affiliation",
    "CompanyContact",
    "Interaction",
    "Deal",
    "Rubric",
    "DiligenceChecklistItem",
    "DealStatus",
    "Fund",
    "Investment",
    "PortfolioMetric",
    "Document",
    "Task",
    "Tag",
    "company_tags",
    "ImportBatch",
    "ImportRow",
    "AuditLog",
    "AiAuditLog",
    "AgentEventLog",
    "AgentPolicy",
    "Notification",
]
