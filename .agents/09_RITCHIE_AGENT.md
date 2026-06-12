# Agent 09: Ritchie Agent Integration

## Goal

Implement the CRM-side Ritchie integration: typed tools, policy, context, `/agent/*` endpoints, MCP/SSE surface, trusted writes, approval proposals, AI audit, idempotency, and event fanout.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `03_AUTH_USERS_PERMISSIONS.md`
- `04_CORE_CRM_API.md`
- `05_PIPELINE_DILIGENCE.md`
- `07_DOCUMENTS_TASKS_NOTIFICATIONS.md`
- `08_SEARCH_ANALYTICS.md`

## May Edit

- `backend/app/api/routes/agent.py`
- `backend/app/agent/`
- `backend/app/services/agent_service.py`
- `backend/app/services/approval_service.py`
- `backend/app/services/audit_service.py`
- `backend/app/core/idempotency.py`
- `backend/app/repositories/agent.py`
- `backend/app/integrations/ritchie_client.py`
- `backend/app/workers/jobs/agent_jobs.py`
- Agent tests and fixtures.

## Avoid

- Direct DB writes from model/free-form text.
- Letting Ritchie access non-agent routes.
- Frontend proposal UI.

## Expected Output

- Typed tool definitions with JSON Schema.
- Permission tier policy: trusted vs approval-required.
- Policy can be changed at runtime if exposed in v1. Do not create a separate admin-only page-access model for v1; all authenticated human users have the same page access.
- Trusted writes are audited before commit.
- Approval-required calls create proposals and never write directly.
- Proposal approve/reject flow uses original idempotency key.
- Agent event log records emitted events and outcomes.
- MCP/SSE endpoint exists for kernelbot consumption.
- `/agent/context` returns ranked context using search service.

## Tests To Add Or Run

- `test_agent_tools.py`
- `test_agent_contracts.py`
- `test_agent_proposals.py`
- `test_agent_replay.py`
- Idempotency tests.

## Definition Of Done

- Ritchie is additive and non-blocking.
- Agent failures are logged and retryable.
- Sensitive writes require human approval.
- No unstructured model text is parsed directly into canonical writes.
