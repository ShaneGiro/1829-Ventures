"""Tool JSON Schemas must exactly match their declared Pydantic models."""

from __future__ import annotations

from app.agent.tools import all_tools


def test_tool_schema_matches_pydantic_model() -> None:
    for tool in all_tools():
        assert tool.json_schema() == tool.input_model.model_json_schema()


def test_write_tools_declare_entity_type() -> None:
    for tool in all_tools():
        if tool.kind == "write":
            assert tool.entity_type is not None, tool.name


def test_schemas_have_required_fields_where_expected() -> None:
    schema = next(t for t in all_tools() if t.name == "add_company_note").json_schema()
    assert "company_id" in schema["required"]
    assert "summary" in schema["required"]
