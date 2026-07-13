"""Tool registry: schema construction and authorized/blocked tags."""

from __future__ import annotations

from app.agent.tools import all_tools, get_tool
from app.core.constants import DEFAULT_BLOCKED_TOOLS, PolicyState


def test_registry_exposes_expected_tools() -> None:
    names = {tool.name for tool in all_tools()}
    assert {
        "search_context",
        "add_company_note",
        "update_company_description",
        "list_company_documents",
        "log_outreach",
        "update_company_enrichment",
        "list_outreach_candidates",
    } <= names


def test_each_tool_has_a_json_schema() -> None:
    for tool in all_tools():
        schema = tool.json_schema()
        assert schema["type"] == "object"
        assert "properties" in schema


def test_sensitive_tools_default_blocked() -> None:
    for tool in all_tools():
        if tool.name in DEFAULT_BLOCKED_TOOLS:
            assert tool.default_state is PolicyState.BLOCKED, tool.name


def test_read_tools_are_authorized_by_default() -> None:
    search = get_tool("search_context")
    assert search is not None
    assert search.kind == "read"
    assert search.default_state is PolicyState.AUTHORIZED


def test_new_agent_write_tools_have_explicit_audit_entities() -> None:
    outreach_tool = get_tool("log_outreach")
    enrichment_tool = get_tool("update_company_enrichment")

    assert outreach_tool is not None
    assert enrichment_tool is not None
    assert outreach_tool.entity_type == "interactions"
    assert enrichment_tool.entity_type == "companies"


def test_get_tool_unknown_returns_none() -> None:
    assert get_tool("does_not_exist") is None
