"""Ritchie `/agent/*` routes.

Tool execution, context retrieval, and tool listing require the Ritchie agent
API key (`CurrentAgent`) — humans and human JWTs cannot call them. Policy
management is a human admin action (`CurrentUser`), so a human can authorize or
block tools at runtime; the agent key cannot change its own permissions.
"""

from __future__ import annotations

import hashlib
import json

from fastapi import APIRouter, Query

from app.agent.mcp import MCP_TRANSPORT
from app.agent.tools import all_tools
from app.core.audit import actor_from_user
from app.core.config import settings
from app.core.constants import AgentEventStatus
from app.core.dependencies import CurrentAgent, CurrentUser, DbSession
from app.integrations.ritchie_client import (
    RitchieUnavailableError,
    build_envelope,
    chat_with_ritchie,
)
from app.repositories import agent as agent_repo
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentContextResult,
    AgentEventLogRead,
    AgentMessageRequest,
    AgentMessageResponse,
    AgentPolicyRead,
    PolicySetRequest,
    ToolDefinition,
    ToolExecuteRequest,
    ToolExecuteResponse,
)
from app.schemas.common import PaginatedResponse
from app.services import agent_policy_service, agent_service, search_service
from app.workers.jobs.agent_jobs import deliver_agent_event

router = APIRouter()


def _payload_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


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


@router.post("/messages", response_model=AgentMessageResponse)
async def send_message_to_ritchie(
    request: AgentMessageRequest,
    db: DbSession,
    user: CurrentUser,
) -> AgentMessageResponse:
    """Queue a human-authored CRM task for kernelbot/Ritchie."""
    payload: dict[str, object] = {
        "prompt": request.prompt,
        "requested_by": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        },
        "crm": {
            "api_base_url": settings.ritchie_crm_api_base_url,
            "mcp_url": settings.ritchie_crm_mcp_url,
            "agent_api_key_required": bool(settings.agent_api_key),
            "mcp_transport": MCP_TRANSPORT,
        },
    }
    event = await agent_repo.create_event(
        db,
        event_type="human_prompt",
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        payload=payload,
        payload_hash=_payload_hash(payload),
        status=AgentEventStatus.PENDING,
    )
    envelope = build_envelope(
        "human_prompt",
        payload,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
    )
    await db.commit()
    deliver_agent_event.delay(envelope, str(event.id))
    return AgentMessageResponse(event_id=event.id, status=event.status)


@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_ritchie_route(
    request: AgentChatRequest,
    db: DbSession,
    user: CurrentUser,
) -> AgentChatResponse:
    """Send a chat turn to Ritchie and wait for a short response."""
    payload: dict[str, object] = {
        "prompt": request.prompt,
        "mode": "chat",
        "instructions": (
            "Respond conversationally to the user. If the request asks you to update CRM "
            "state, use the CRM MCP tools first, then summarize what changed. Write a "
            "concise final answer to the provided result path."
        ),
        "requested_by": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
        },
        "crm": {
            "api_base_url": settings.ritchie_crm_api_base_url,
            "mcp_url": settings.ritchie_crm_mcp_url,
            "agent_api_key_required": bool(settings.agent_api_key),
            "mcp_transport": MCP_TRANSPORT,
        },
    }
    event = await agent_repo.create_event(
        db,
        event_type="human_chat",
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        payload=payload,
        payload_hash=_payload_hash(payload),
        status=AgentEventStatus.PROCESSING,
    )
    envelope = build_envelope(
        "human_chat",
        payload,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
    )
    await db.commit()

    try:
        result = chat_with_ritchie(
            envelope,
            timeout=settings.ritchie_chat_timeout_seconds,
        )
    except RitchieUnavailableError as exc:
        event.status = AgentEventStatus.AGENT_UNAVAILABLE
        event.rationale = str(exc)
        await db.commit()
        return AgentChatResponse(
            event_id=event.id,
            status=event.status,
            message="Ritchie is not available for chat right now.",
        )

    message = str(result.get("summary") or "").strip() or "Ritchie finished without a reply."
    exit_code = int(result.get("exit") or 0)
    event.status = AgentEventStatus.PROCESSED if exit_code == 0 else AgentEventStatus.FAILED
    if exit_code == 124:
        message = (
            "Ritchie did not respond before the chat timeout. Check that Claude is "
            "logged in inside kernelbot."
        )
    event.response_summary = message
    await db.commit()
    return AgentChatResponse(
        event_id=event.id,
        status=event.status,
        message=message,
        elapsed_ms=int(result["elapsed_ms"]) if result.get("elapsed_ms") is not None else None,
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
