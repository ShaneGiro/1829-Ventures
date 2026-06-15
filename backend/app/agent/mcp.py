"""MCP server surface for kernelbot, using the Streamable HTTP transport.

SSE is deprecated in the MCP spec, so we expose the tools over Streamable HTTP.
Each MCP tool delegates to `agent_service.execute_tool`, so the binary policy
gate, AI audit, and idempotency apply identically whether a tool is called via
MCP or the REST `/agent` routes.
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.agent.tools import all_tools
from app.core.database import AsyncSessionLocal
from app.models.user import User

MCP_TRANSPORT = "streamable-http"
MCP_SERVER_NAME = "ritchie-crm"


async def _resolve_agent_user(session: Any) -> User:
    user = await session.scalar(
        select(User).where(User.is_agent.is_(True), User.is_active.is_(True))
    )
    if user is None:
        raise RuntimeError("No active agent identity configured")
    return cast(User, user)


def _make_tool_callable(tool_name: str) -> Any:
    async def _call(payload: dict[str, Any], event_id: str | None = None) -> dict[str, Any]:
        from app.services import agent_service

        async with AsyncSessionLocal() as session:
            agent_user = await _resolve_agent_user(session)
            execution = await agent_service.execute_tool(
                session,
                agent_user=agent_user,
                tool_name=tool_name,
                payload=payload,
                event_id=event_id or str(uuid.uuid4()),
                source="mcp",
            )
            return {
                "status": execution.status,
                "data": execution.data,
                "rationale": execution.rationale,
                "idempotency_key": execution.idempotency_key,
            }

    _call.__name__ = f"tool_{tool_name}"
    return _call


def build_mcp_server() -> FastMCP:
    """Construct the FastMCP server with every registered Ritchie tool."""
    server = FastMCP(MCP_SERVER_NAME)
    for tool in all_tools():
        server.add_tool(
            _make_tool_callable(tool.name),
            name=tool.name,
            description=f"[{tool.kind}/{tool.default_state}] {tool.description}",
        )
    return server


def get_mcp_app() -> Any:
    """ASGI app for the Streamable HTTP MCP transport (mountable under FastAPI)."""
    return build_mcp_server().streamable_http_app()
