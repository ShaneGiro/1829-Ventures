"""Ritchie `/agent/*` routes.

Tool execution, context retrieval, and tool listing require the Ritchie agent
API key (`CurrentAgent`) — humans and human JWTs cannot call them. Policy
management is a human admin action (`CurrentUser`), so a human can authorize or
block tools at runtime; the agent key cannot change its own permissions.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.agent.mcp import MCP_TRANSPORT
from app.agent.tools import all_tools
from app.core.audit import actor_from_user
from app.core.dependencies import CurrentAgent, CurrentUser, DbSession
from app.repositories import agent as agent_repo
from app.schemas.agent import (
    AgentContextResult,
    AgentEventLogRead,
    AgentPolicyRead,
    PolicySetRequest,
    ToolDefinition,
    ToolExecuteRequest,
    ToolExecuteResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import agent_policy_service, agent_service, search_service

router = APIRouter()


@router.get("/tools", response_model=list[ToolDefinition])
async def list_tools(db: DbSession, _agent: CurrentAgent) -> list[ToolDefinition]:
    definitions: list[ToolDefinition] = []
    for tool in all_tools():
        state = await agent_policy_service.get_effective_state(db, tool.name)
        definitions.append(
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                kind=tool.kind,
                state=state,
                entity_type=tool.entity_type,
                input_schema=tool.json_schema(),
            )
        )
    return definitions


@router.post("/tools/{tool_name}", response_model=ToolExecuteResponse)
async def execute_tool(
    tool_name: str,
    request: ToolExecuteRequest,
    db: DbSession,
    agent: CurrentAgent,
) -> ToolExecuteResponse:
    import uuid

    execution = await agent_service.execute_tool(
        db,
        agent_user=agent,
        tool_name=tool_name,
        payload=request.payload,
        event_id=request.event_id or str(uuid.uuid4()),
        confidence=request.confidence,
        source=request.source,
    )
    return ToolExecuteResponse(
        status=execution.status,
        tool=execution.tool,
        data=execution.data,
        rationale=execution.rationale,
        idempotency_key=execution.idempotency_key,
        ai_audit_id=execution.ai_audit_id,
        event_id=execution.event_id,
    )


@router.get("/context", response_model=list[AgentContextResult])
async def agent_context(
    db: DbSession,
    _agent: CurrentAgent,
    query: str = Query(min_length=1),
    limit: int = Query(default=8, ge=1, le=25),
) -> list[AgentContextResult]:
    results = await search_service.retrieve_context(db, query, limit=limit)
    return [
        AgentContextResult(
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            title=r.title,
            snippet=r.snippet,
            rank=r.rank,
        )
        for r in results
    ]


@router.get("/events", response_model=PaginatedResponse[AgentEventLogRead])
async def list_events(
    db: DbSession,
    _user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[AgentEventLogRead]:
    events = await agent_repo.list_events(db, limit=limit, offset=offset)
    total = await agent_repo.count_events(db)
    return PaginatedResponse(
        items=[AgentEventLogRead.model_validate(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


# ─── Policy management (human admin) ──────────────────────────────────────────
@router.get("/policies", response_model=list[AgentPolicyRead])
async def list_policies(db: DbSession, _user: CurrentUser) -> list[AgentPolicyRead]:
    policies = await agent_repo.list_policies(db)
    return [AgentPolicyRead.model_validate(p) for p in policies]


@router.put("/policies", response_model=AgentPolicyRead)
async def set_policy(
    request: PolicySetRequest, db: DbSession, user: CurrentUser
) -> AgentPolicyRead:
    await agent_policy_service.set_state(
        db,
        tool=request.tool,
        field_name=request.field_name,
        state=request.state,
        actor=actor_from_user(user),
        actor_id=user.id,
    )
    policy = await agent_repo.get_policy(db, request.tool, request.field_name)
    assert policy is not None
    return AgentPolicyRead.model_validate(policy)


@router.get("/mcp-info")
async def mcp_info(_agent: CurrentAgent) -> dict[str, str]:
    """Expose the MCP transport in use (Streamable HTTP) for kernelbot discovery."""
    return {"transport": MCP_TRANSPORT}
