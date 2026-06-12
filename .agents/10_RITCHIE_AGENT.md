# Agent 10: Ritchie Agent Integration

## Goal

Implement the CRM-side Ritchie integration: typed tools, the binary authorization policy, RAG context, `/agent/*` endpoints, the Streamable HTTP MCP surface, authorized writes, AI audit, idempotency, and event fanout.

## Read First

- `planning/PLAN_v1.md` (AI Agent Integration section — the methodology is fully specified there)
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
- `backend/app/services/agent_policy_service.py`
- `backend/app/services/audit_service.py` (AI audit paths only)
- `backend/app/core/idempotency.py`
- `backend/app/repositories/agent.py`
- `backend/app/integrations/ritchie_client.py`
- `backend/app/workers/jobs/agent_jobs.py`
- Agent tests and fixtures.

## Avoid

- Building any proposal, approval-queue, or approve/reject-email workflow — this was removed from the plan. The policy is strictly binary.
- Direct DB writes from model/free-form text.
- Letting Ritchie access non-agent routes.
- Frontend UI.

## Expected Output

- Typed tool definitions with JSON Schema, each tagged `authorized` or `blocked`.
- Binary authorization policy stored in the database (`agent_policy` model): every tool/field is either `authorized` (executes directly) or `blocked` (rejected at the policy gate before any service logic runs).
- Policy is runtime-configurable through `agent_policy_service`: changes are audited and take effect immediately, no restart. Do not create a separate admin-only page-access model for v1.
- Sensitive defaults are blocked: investment amount, valuation, ownership, deal stage/status, legal terms, investment recommendation, portfolio marks, rubric scores.
- Authorized writes record intent in the AI audit log (status `pending`) before the canonical write, then update to `committed` or `failed`.
- Blocked calls never write; each rejection is logged as `policy_blocked` in the agent event log with tool, payload hash, rationale, and confidence.
- Every write carries an idempotency key (event ID + tool name + entity ID); duplicate keys are no-ops.
- Agent event log records every emitted event and its processing outcome.
- MCP server uses the **Streamable HTTP transport** (SSE is deprecated in the MCP spec) for kernelbot consumption.
- `/agent/context` returns ranked RAG context using the search service.
- Event fanout: backend state changes enqueue JSON envelopes to kernelbot via `ritchie_client`.
- Rate limits per tool type enforced via the Redis token-bucket middleware (reads 120/min, authorized writes 60/min).
- Graceful degradation: agent failures are retried with backoff, logged as `agent_unavailable`, and never block user-facing functionality.

## Tests To Add Or Run

- `test_agent_tools.py`: tool schema construction, authorized/blocked tags.
- `test_agent_contracts.py`: tool JSON Schemas match their Pydantic models.
- `test_agent_policy.py`: blocked tools never write; runtime policy flips take effect immediately and are audited.
- `test_agent_policy_flow.py` (integration): blocked call rejected and logged → policy authorized → retried call executes with original idempotency key.
- `test_agent_replay.py`: replay recorded payloads without live Claude API calls.
- `test_idempotency.py`: stable keys, duplicate-write prevention.

## Definition Of Done

- Ritchie is additive and non-blocking.
- Agent failures are logged and retryable.
- Blocked tools/fields cannot write under any code path — enforced at the policy gate, not by convention.
- No unstructured model text is parsed directly into canonical writes.
