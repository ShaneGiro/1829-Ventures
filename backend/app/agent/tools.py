"""Typed Ritchie tool definitions and registry.

Each tool declares a Pydantic input model (its JSON Schema is the wire contract),
a kind (read or write), a default authorization state, and an async handler that
performs the canonical work. Sensitive writes default to BLOCKED; the runtime
policy (agent_policy) can flip any tool/field without a restart.

Handlers never parse free-form model text — they receive a validated Pydantic
payload. Write handlers go through repositories/services so audit and invariants
are preserved.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.constants import (
    AlumniFounderStatus,
    FollowUpStatus,
    InteractionDirection,
    InteractionType,
    OperationalStatus,
    PolicyState,
    TaskPriority,
)
from app.core.exceptions import NotFoundError
from app.models.interaction import Interaction
from app.models.investment import Investment
from app.models.rubric import Rubric
from app.models.task import Task
from app.models.user import User
from app.repositories import base
from app.repositories import companies as company_repo
from app.repositories import documents as document_repo
from app.repositories import interactions as interaction_repo
from app.repositories import tasks as task_repo
from app.services import audit_service, outreach_candidate_service, search_service

ToolKind = str  # "read" | "write"


@dataclass(frozen=True)
class ToolResult:
    """Outcome of a tool invocation.

    For writes, entity/old/new feed the AI audit log; `data` is the API response.
    """

    data: Any
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None


Handler = Callable[[AsyncSession, BaseModel, User], Awaitable[ToolResult]]


@dataclass(frozen=True)
class AgentTool:
    name: str
    description: str
    kind: ToolKind
    input_model: type[BaseModel]
    handler: Handler
    default_state: PolicyState
    entity_type: str | None = None

    def json_schema(self) -> dict[str, Any]:
        return self.input_model.model_json_schema()


# ─── Tool input models ────────────────────────────────────────────────────────
class SearchContextInput(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=8, ge=1, le=25)


class AddCompanyNoteInput(BaseModel):
    company_id: uuid.UUID
    summary: str = Field(min_length=1, max_length=512)
    body: str | None = None


class UpdateCompanyDescriptionInput(BaseModel):
    company_id: uuid.UUID
    description: str = Field(min_length=1)


class CreateFollowupTaskInput(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    company_id: uuid.UUID | None = None
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM


class UpdateInvestmentAmountInput(BaseModel):
    investment_id: uuid.UUID
    amount: Decimal = Field(ge=0)


class UpdateRubricScoreInput(BaseModel):
    rubric_id: uuid.UUID
    field_name: str
    score: int = Field(ge=1, le=5)


class ListCompanyDocumentsInput(BaseModel):
    company_id: uuid.UUID
    limit: int = Field(default=25, ge=1, le=100)


class ListOutreachCandidatesInput(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)


class LogOutreachInput(BaseModel):
    company_id: uuid.UUID
    person_id: uuid.UUID | None = None
    summary: str = Field(min_length=1, max_length=512)
    body: str | None = None
    channel: str = Field(min_length=1, max_length=32)
    occurred_at: datetime | None = None
    follow_up_status: FollowUpStatus = FollowUpStatus.NONE


class UpdateCompanyEnrichmentInput(BaseModel):
    company_id: uuid.UUID
    alumni_founder_status: AlumniFounderStatus | None = None
    alumni_founder_confidence: float | None = Field(default=None, ge=0, le=1)
    alumni_founder_evidence: dict[str, Any] | None = None
    alumni_founder_verified_at: datetime | None = None
    operational_status: OperationalStatus | None = None
    operational_confidence: float | None = Field(default=None, ge=0, le=1)
    operational_evidence: dict[str, Any] | None = None
    operational_verified_at: datetime | None = None
    rubric_fit_score: float | None = Field(default=None, ge=0, le=100)
    thesis_alignment_score: float | None = Field(default=None, ge=0, le=100)
    fit_score_confidence: float | None = Field(default=None, ge=0, le=1)
    fit_score_reasons: list[str] | None = None


# ─── Handlers ─────────────────────────────────────────────────────────────────
async def _search_context(session: AsyncSession, payload: BaseModel, _actor: User) -> ToolResult:
    assert isinstance(payload, SearchContextInput)
    results = await search_service.retrieve_context(session, payload.query, limit=payload.limit)
    return ToolResult(
        data=[
            {
                "entity_type": r.entity_type,
                "entity_id": str(r.entity_id),
                "title": r.title,
                "snippet": r.snippet,
                "rank": r.rank,
            }
            for r in results
        ]
    )


async def _add_company_note(session: AsyncSession, payload: BaseModel, actor: User) -> ToolResult:
    assert isinstance(payload, AddCompanyNoteInput)
    company = await company_repo.get_company(session, payload.company_id)
    if company is None:
        raise NotFoundError("Company not found")
    interaction = Interaction(
        interaction_type=InteractionType.NOTE,
        summary=payload.summary,
        body=payload.body,
        company_id=payload.company_id,
        provenance={"source": "ritchie"},
    )
    await interaction_repo.create_interaction(session, interaction)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=interaction)
    return ToolResult(
        data={"interaction_id": str(interaction.id)},
        entity_type="interactions",
        entity_id=interaction.id,
        new_value={"summary": payload.summary},
    )


async def _update_company_description(
    session: AsyncSession, payload: BaseModel, actor: User
) -> ToolResult:
    assert isinstance(payload, UpdateCompanyDescriptionInput)
    company = await company_repo.get_company(session, payload.company_id)
    if company is None:
        raise NotFoundError("Company not found")
    old = company.description
    company.description = payload.description
    await audit_service.record_update(
        session,
        actor=actor_from_user(actor),
        entity=company,
        changes={"description": (old, payload.description)},
    )
    return ToolResult(
        data={"company_id": str(company.id)},
        entity_type="companies",
        entity_id=company.id,
        old_value={"description": old},
        new_value={"description": payload.description},
    )


async def _create_followup_task(
    session: AsyncSession, payload: BaseModel, actor: User
) -> ToolResult:
    assert isinstance(payload, CreateFollowupTaskInput)
    from app.core.constants import ActorType

    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        company_id=payload.company_id,
        created_by_type=ActorType.AGENT,
        created_by_id=actor.id,
    )
    await task_repo.create_task(session, task)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=task)
    return ToolResult(
        data={"task_id": str(task.id)},
        entity_type="tasks",
        entity_id=task.id,
        new_value={"title": payload.title},
    )


async def _update_investment_amount(
    session: AsyncSession, payload: BaseModel, actor: User
) -> ToolResult:
    assert isinstance(payload, UpdateInvestmentAmountInput)
    investment = await base.get_by_id(session, Investment, payload.investment_id)
    if investment is None:
        raise NotFoundError("Investment not found")
    old = investment.amount
    # Numeric column stores Decimal at runtime; model annotation is float | None.
    investment.amount = cast(float, payload.amount)
    await audit_service.record_update(
        session,
        actor=actor_from_user(actor),
        entity=investment,
        changes={"amount": (old, payload.amount)},
    )
    return ToolResult(
        data={"investment_id": str(investment.id)},
        entity_type="investments",
        entity_id=investment.id,
        old_value={"amount": str(old) if old is not None else None},
        new_value={"amount": str(payload.amount)},
    )


async def _update_rubric_score(
    session: AsyncSession, payload: BaseModel, actor: User
) -> ToolResult:
    assert isinstance(payload, UpdateRubricScoreInput)
    rubric = await base.get_by_id(session, Rubric, payload.rubric_id)
    if rubric is None:
        raise NotFoundError("Rubric not found")
    if not hasattr(rubric, payload.field_name):
        raise NotFoundError(f"Unknown rubric field: {payload.field_name}")
    old = getattr(rubric, payload.field_name)
    setattr(rubric, payload.field_name, payload.score)
    await audit_service.record_update(
        session,
        actor=actor_from_user(actor),
        entity=rubric,
        changes={payload.field_name: (old, payload.score)},
    )
    return ToolResult(
        data={"rubric_id": str(rubric.id)},
        entity_type="rubrics",
        entity_id=rubric.id,
        old_value={payload.field_name: old},
        new_value={payload.field_name: payload.score},
    )


async def _list_company_documents(
    session: AsyncSession, payload: BaseModel, _actor: User
) -> ToolResult:
    assert isinstance(payload, ListCompanyDocumentsInput)
    documents = await document_repo.list_documents(
        session, limit=payload.limit, offset=0, company_id=payload.company_id
    )
    return ToolResult(
        data=[
            {
                "document_id": str(document.id),
                "filename": document.filename,
                "content_type": document.content_type,
                "status": document.status,
            }
            for document in documents
        ]
    )


async def _log_outreach(session: AsyncSession, payload: BaseModel, actor: User) -> ToolResult:
    assert isinstance(payload, LogOutreachInput)
    interaction = Interaction(
        interaction_type=InteractionType.TOUCHPOINT,
        summary=payload.summary,
        body=payload.body,
        occurred_at=payload.occurred_at,
        company_id=payload.company_id,
        person_id=payload.person_id,
        channel=payload.channel,
        direction=InteractionDirection.OUTBOUND,
        follow_up_status=payload.follow_up_status,
        created_by_id=actor.id,
        provenance={"source": "ritchie_mcp"},
    )
    await interaction_repo.create_interaction(session, interaction)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=interaction)
    return ToolResult(
        data={"interaction_id": str(interaction.id)},
        entity_type="interactions",
        entity_id=interaction.id,
        new_value={"summary": payload.summary, "channel": payload.channel},
    )


async def _update_company_enrichment(
    session: AsyncSession, payload: BaseModel, actor: User
) -> ToolResult:
    assert isinstance(payload, UpdateCompanyEnrichmentInput)
    company = await company_repo.get_company(session, payload.company_id)
    if company is None:
        raise NotFoundError("Company not found")
    updates = payload.model_dump(exclude={"company_id"}, exclude_none=True)
    changes: dict[str, tuple[Any, Any]] = {}
    for field_name, value in updates.items():
        old_value = getattr(company, field_name)
        if old_value != value:
            setattr(company, field_name, value)
            changes[field_name] = (old_value, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=company, changes=changes
        )
    return ToolResult(
        data={"company_id": str(company.id), "updated_fields": sorted(changes)},
        entity_type="companies",
        entity_id=company.id,
        old_value={name: old for name, (old, _new) in changes.items()},
        new_value={name: new for name, (_old, new) in changes.items()},
    )


async def _list_outreach_candidates(
    session: AsyncSession, payload: BaseModel, _actor: User
) -> ToolResult:
    assert isinstance(payload, ListOutreachCandidatesInput)
    items, total = await outreach_candidate_service.list_candidates(
        session, limit=payload.limit, offset=0
    )
    return ToolResult(
        data={
            "total": total,
            "items": [
                {
                    "company_id": str(item.company.id),
                    "company_name": item.company.name,
                    "score": item.score,
                    "why_this_company": item.why_this_company,
                    "warnings": item.warnings,
                }
                for item in items
            ],
        }
    )


# ─── Registry ─────────────────────────────────────────────────────────────────
_TOOLS: tuple[AgentTool, ...] = (
    AgentTool(
        name="search_context",
        description="Retrieve ranked CRM context (companies, interactions, deals) for a query.",
        kind="read",
        input_model=SearchContextInput,
        handler=_search_context,
        default_state=PolicyState.AUTHORIZED,
    ),
    AgentTool(
        name="add_company_note",
        description="Attach a note interaction to a company.",
        kind="write",
        input_model=AddCompanyNoteInput,
        handler=_add_company_note,
        default_state=PolicyState.AUTHORIZED,
        entity_type="interactions",
    ),
    AgentTool(
        name="update_company_description",
        description="Update a company's description.",
        kind="write",
        input_model=UpdateCompanyDescriptionInput,
        handler=_update_company_description,
        default_state=PolicyState.AUTHORIZED,
        entity_type="companies",
    ),
    AgentTool(
        name="create_followup_task",
        description="Create a follow-up task, optionally linked to a company.",
        kind="write",
        input_model=CreateFollowupTaskInput,
        handler=_create_followup_task,
        default_state=PolicyState.AUTHORIZED,
        entity_type="tasks",
    ),
    AgentTool(
        name="update_investment_amount",
        description="Update an investment's amount (sensitive — blocked by default).",
        kind="write",
        input_model=UpdateInvestmentAmountInput,
        handler=_update_investment_amount,
        default_state=PolicyState.BLOCKED,
        entity_type="investments",
    ),
    AgentTool(
        name="update_rubric_score",
        description="Update a rubric sub-score (sensitive — blocked by default).",
        kind="write",
        input_model=UpdateRubricScoreInput,
        handler=_update_rubric_score,
        default_state=PolicyState.BLOCKED,
        entity_type="rubrics",
    ),
    AgentTool(
        name="list_company_documents",
        description="List confirmed document metadata attached to a company.",
        kind="read",
        input_model=ListCompanyDocumentsInput,
        handler=_list_company_documents,
        default_state=PolicyState.AUTHORIZED,
    ),
    AgentTool(
        name="log_outreach",
        description="Record an outbound company/person touch with channel and follow-up state.",
        kind="write",
        input_model=LogOutreachInput,
        handler=_log_outreach,
        default_state=PolicyState.AUTHORIZED,
        entity_type="interactions",
    ),
    AgentTool(
        name="update_company_enrichment",
        description="Record evidence-backed founder, operational, and fit-score enrichment.",
        kind="write",
        input_model=UpdateCompanyEnrichmentInput,
        handler=_update_company_enrichment,
        default_state=PolicyState.AUTHORIZED,
        entity_type="companies",
    ),
    AgentTool(
        name="list_outreach_candidates",
        description="List ranked, explainable outreach candidates.",
        kind="read",
        input_model=ListOutreachCandidatesInput,
        handler=_list_outreach_candidates,
        default_state=PolicyState.AUTHORIZED,
    ),
)

TOOL_REGISTRY: dict[str, AgentTool] = {tool.name: tool for tool in _TOOLS}


def get_tool(name: str) -> AgentTool | None:
    return TOOL_REGISTRY.get(name)


def all_tools() -> list[AgentTool]:
    return list(_TOOLS)
