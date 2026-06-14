# Model-to-Model Handoff For Gemini

Last updated: 2026-06-14 by Codex.

This file is the current handoff for continuing implementation of the 1829
Ventures CRM. It intentionally replaces the older running log. Read this file
first, then read:

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `CONTRIBUTING.md`
- `.agents/README.md`
- The specific `.agents/NN_*.md` brief for the next agent you run

## Current Repository State

Repo root:

```text
/Users/shanegirolamo/Downloads/1829 Ventures Software/1829-Ventures
```

Current branch:

```text
v1
```

Current local commit:

```text
06c25b4 Fix integrated task notification formatting
```

Remote state:

```text
v1 is ahead of origin/v1 by 4 commits.
main is older than v1.
Nothing has been pushed after Agent 08 integration.
```

Worktrees:

```text
Only the main worktree remains.
Agent 04/05/06 and Agent 07/08 worktrees were pruned after successful merge.
```

Important: continue all v1 implementation from branch `v1`, not `main`. The user
wants all v1 work on `v1`.

## Recent Commit History

Relevant local commits, newest first:

```text
06c25b4 (HEAD -> v1) Fix integrated task notification formatting
d3ec923 Merge branch 'agent/08-search-analytics' into v1
da75ea3 (agent/08-search-analytics) Implement search and analytics services
562ef7c (agent/07-documents-tasks-notifications) Implement task notifications and document storage
73627fd (origin/v1, main) Fix integrated Dealroom test formatting
804cadd Merge branch 'agent/06-dealroom-imports'
926dd74 Merge branch 'agent/05-pipeline-diligence'
7b23a0f (agent/04-core-crm-api) Implement core CRM API
399da9b (agent/06-dealroom-imports) Implement Dealroom import preview and commit
f5fdcc5 (agent/05-pipeline-diligence) Implement pipeline diligence workflows
815507a (origin/main, origin/HEAD, agent/03-auth-users-permissions) Agent 03: auth users and permissions
a7938ea docs: add worktree + orchestration plan to MODEL_COMMS handoff
6179146 docs: MODEL_COMMS handoff for Agent 03 (Claude -> Codex 5.5)
9812eb1 Agent 02: data model, schemas, and initial migration
e992d61 Agent 01: backend foundation
52e45a6 Updated agents
```

## What Has Been Implemented

Backend Agents 01 through 08 are implemented and merged into `v1`.

### Agent 01: Backend Foundation

Commit: `e992d61`

Implemented:

- FastAPI app factory and router mounting.
- Health routes.
- Core config via Pydantic settings.
- Dual database engines:
  - Async SQLAlchemy engine/session for FastAPI.
  - Sync SQLAlchemy engine/session for Celery and Alembic.
- PyJWT helpers and API-key hashing helpers.
- Typed application exceptions.
- JSON/request-ID logging.
- Redis-backed rate-limit middleware.
- Celery app bootstrap.
- Docker Compose services for API, worker, Postgres/PostGIS/pgvector, Redis, MinIO.
- CI, Makefile, `.env.example`, backup script, Dockerfiles.

Important files:

- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/security.py`
- `backend/app/api/router.py`
- `backend/app/api/middleware.py`
- `backend/app/workers/celery_app.py`

### Agent 02: Models, Schemas, Migrations

Commit: `9812eb1`

Implemented:

- 23 SQLAlchemy models plus `company_tags` join table.
- Initial Alembic schema migration:
  - `backend/alembic/versions/4d6ffdeb3a50_initial_schema.py`
- Pydantic schemas for core entities.
- Domain constants/enums in `backend/app/core/constants.py`.
- Seed script for funds/statuses.

Key model areas:

- CRM: `User`, `Company`, `Person`, `Affiliation`, `CompanyContact`,
  `Interaction`.
- Deals/diligence: `Deal`, `Rubric`, `DiligenceChecklistItem`, `DealStatus`.
- Fund/portfolio: `Fund`, `Investment`, `PortfolioMetric`.
- Documents/tasks/tags/imports/audit/agent/notifications.

Migration gotchas already handled:

- Postgres image builds PostGIS plus pgvector.
- Alembic ignores PostGIS tiger/topology tables.
- GeoAlchemy2 manages the `companies.location` GiST index; do not add a duplicate
  explicit index for it.
- Generated migrations involving GeoAlchemy2/pgvector may need manual imports.

### Agent 03: Auth, Users, Permissions

Commit: `815507a`

Implemented:

- Google OAuth wrapper.
- Auth routes:
  - `/api/auth/login`
  - `/api/auth/callback`
  - `/api/auth/refresh`
  - `/api/auth/logout`
  - `/api/auth/me`
- User routes:
  - `/api/users`
  - `/api/users/me`
  - `/api/users/{user_id}`
- User repository.
- Central v1 permission guard.
- Human JWT/session-cookie auth.
- Scoped Ritchie API-key dependency.
- Agent API keys are rejected from ordinary human routes with 403.
- `backend/scripts/rotate_agent_key.py`.
- Starlette `SessionMiddleware` for OAuth state.
- `itsdangerous` dependency for signed session cookies.

Important rule: authenticated human users have equal access in v1. Role fields
exist for the future but are not currently used to restrict ordinary user pages.

### Agent 04: Core CRM API

Commit: `7b23a0f`

Implemented:

- CRUD routes and services for:
  - Companies
  - People
  - Company contacts
  - Affiliations
  - Interactions
  - Funds
  - Investments
  - Portfolio metrics
  - Documents metadata
- Repositories for core CRM entities.
- Audit service and audit context.
- Company completeness calculation.
- Primary company contact behavior.
- Document metadata and presigned-upload service boundary.
- Soft archive endpoints where models support `archived_at`.

Important files:

- `backend/app/api/routes/companies.py`
- `backend/app/api/routes/people.py`
- `backend/app/api/routes/interactions.py`
- `backend/app/api/routes/investments.py`
- `backend/app/api/routes/portfolio_metrics.py`
- `backend/app/api/routes/documents.py`
- `backend/app/services/company_service.py`
- `backend/app/services/document_service.py`
- `backend/app/services/audit_service.py`
- `backend/app/core/audit.py`
- Core repositories under `backend/app/repositories/`

### Agent 05: Pipeline And Diligence

Commit: `f5fdcc5`, merged via `926dd74`

Implemented:

- Deal CRUD.
- Configurable deal status API.
- Relationship/investment status service logic.
- Review-needed triage:
  - Start investment review.
  - Monitor.
  - Pass.
- Pass requires reason tags.
- Monitor requires future next-check date and creates a reminder task.
- Start-review creates/uses a deal, moves to initial review, initializes rubric
  and checklist.
- Rubric gate enforcement.
- 15 sub-score weighted scoring and composite thresholds.
- Diligence checklist initialization and completion tracking.

Important files:

- `backend/app/api/routes/deals.py`
- `backend/app/api/routes/deal_statuses.py`
- `backend/app/services/deal_service.py`
- `backend/app/services/pipeline_service.py`
- `backend/app/services/diligence_service.py`
- `backend/app/repositories/deals.py`
- `backend/app/repositories/deal_statuses.py`

### Agent 06: Dealroom Imports

Commit: `399da9b`, merged via `804cadd`

Implemented:

- Dealroom CSV parser and import flow.
- Metadata row/header detection for the provided CSV.
- Semicolon-delimited field parsing.
- Parallel founder/funding arrays.
- Latitude/longitude handling.
- Dealroom taxonomy mapping to 1829 sector taxonomy.
- Import preview and commit separation.
- Partial commit support.
- Raw row/provenance preservation.
- Imported companies start as `imported_unreviewed`.
- Celery job registration for Dealroom import jobs.

Important files:

- `backend/app/api/routes/imports.py`
- `backend/app/integrations/dealroom_csv.py`
- `backend/app/services/dealroom_import_service.py`
- `backend/app/repositories/imports.py`
- `backend/app/workers/jobs/dealroom_import_jobs.py`

### Agent 07: Documents, Tasks, Notifications

Commit: `562ef7c`, merged into `v1` before Agent 08.

Implemented:

- Task API route.
- Task service and repository.
- Notification service and repository.
- Storage abstraction.
- MinIO S3-compatible storage adapter.
- SendGrid integration wrapper.
- Notification Celery jobs and registration.
- Document service extended for storage/presigned-upload behavior.
- Task completion history fields.
- Task model/schema updates.
- Notification/document schema updates.
- Alembic migration:
  - `backend/alembic/versions/8f3c2b71e4a9_task_completion_history.py`

Important files:

- `backend/app/api/routes/tasks.py`
- `backend/app/services/task_service.py`
- `backend/app/services/notification_service.py`
- `backend/app/integrations/storage.py`
- `backend/app/integrations/minio_storage.py`
- `backend/app/integrations/sendgrid.py`
- `backend/app/workers/jobs/notification_jobs.py`

### Agent 08: Search And Analytics

Commit: `da75ea3`, merged via `d3ec923`.

Implemented:

- Analytics API route.
- Search service:
  - Postgres full-text keyword search.
  - pgvector semantic/context retrieval.
- Lazy configurable sentence-transformer embedding integration.
- Embedding worker jobs:
  - Companies.
  - Interactions.
  - Backfill missing embeddings.
- Analytics repository/service/routes for:
  - Pipeline.
  - Portfolio.
  - Source.
  - Sector.
  - Interaction cadence.
  - Thesis fit.
  - Agent activity.
- Celery job registration for embedding and analytics jobs.
- Environment settings for embeddings.
- Alembic migration:
  - `backend/alembic/versions/7a8f1b2c3d4e_search_vector_indexes.py`

Important files:

- `backend/app/api/routes/analytics.py`
- `backend/app/services/search_service.py`
- `backend/app/services/analytics_service.py`
- `backend/app/repositories/analytics.py`
- `backend/app/integrations/embeddings.py`
- `backend/app/workers/jobs/embedding_jobs.py`
- `backend/app/workers/jobs/analytics_jobs.py`

## Verification Already Run

After Agents 07 and 08 were merged into `v1`, Codex ran:

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/ruff format --check app tests scripts
DEBUG=false .venv/bin/mypy
DEBUG=false .venv/bin/python -m pytest tests/unit -q --no-cov
DEBUG=false .venv/bin/python -m pytest -q
```

Results:

```text
ruff check: passed
ruff format --check: passed
mypy: passed
unit tests: 57 passed
full tests with local Postgres: 62 passed
```

The full pytest run required access to localhost Postgres and was run with
Docker Postgres/Redis available.

Important environment quirk:

```text
The ambient shell has DEBUG=release in some sessions.
Pydantic settings reject that because DEBUG must be boolean.
Use DEBUG=false for backend commands unless the environment is cleaned.
```

## Immediate Known Issue: Alembic Has Two Heads

This is the first thing Gemini should address before or during the next backend
work.

Current Alembic heads:

```text
7a8f1b2c3d4e (head)
8f3c2b71e4a9 (head)
```

Why:

- Agent 07 added `8f3c2b71e4a9_task_completion_history.py`.
- Agent 08 added `7a8f1b2c3d4e_search_vector_indexes.py`.
- Both currently have:

```text
down_revision = "4d6ffdeb3a50"
```

This is expected from parallel branches, but it must be reconciled before relying
on Alembic upgrade/check in CI or deployment.

Recommended fix:

- Create a no-op Alembic merge migration on `v1` with both revisions as
  `down_revision`, or restamp one migration after the other if you prefer a
  linear migration history.
- A merge migration is probably least invasive because the two migrations touch
  unrelated schema/index areas.
- After the fix, verify:

```bash
cd backend
DEBUG=false .venv/bin/alembic heads
DEBUG=false .venv/bin/alembic upgrade head
DEBUG=false .venv/bin/alembic check
```

Expected after fix:

```text
Only one Alembic head.
No new upgrade operations detected.
```

## Local Environment Notes

Python/tooling:

- The repo targets Python 3.12 in `backend/pyproject.toml`.
- Local environment during Codex work had Python 3.14 available, but tests passed
  in `backend/.venv`.
- Do not introduce PEP 695 syntax (`class Foo[T]`, `type X = ...`) because prior
  local runs used Python 3.11 and the project intentionally avoided that syntax.
- Ruff ignores UP046/UP047 for this reason.

Backend venv:

```bash
cd "/Users/shanegirolamo/Downloads/1829 Ventures Software/1829-Ventures/backend"
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt
```

For faster local verification, Codex installed the lightweight subset plus needed
declared dependencies into `backend/.venv`. Full requirements include heavy AI
dependencies (`sentence-transformers` and torch note).

Docker:

```bash
cd "/Users/shanegirolamo/Downloads/1829 Ventures Software/1829-Ventures"
docker compose up -d postgres redis
```

Postgres image builds from `docker/postgres/Dockerfile` so pgvector is available.

Settings:

- `.env.example` has auth, DB, storage, email, and embedding settings.
- Settings load `.env` from current working directory, so running from `backend/`
  may need exported env vars or a `backend/.env`.
- Use `DEBUG=false` in commands if the shell has `DEBUG=release`.

Common verification commands:

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/ruff format --check app tests scripts
DEBUG=false .venv/bin/mypy
DEBUG=false .venv/bin/python -m pytest tests/unit -q --no-cov
DEBUG=false .venv/bin/python -m pytest -q
```

## Architectural Rules To Preserve

- Routes handle HTTP only.
- Services own business logic, permissions, audit, workflow transitions, and
  source-of-truth behavior.
- Repositories isolate SQLAlchemy queries.
- Workers handle slow/background work.
- Every create/update/archive should be audited with actor, timestamp, old/new
  values, and reason/context where relevant.
- Core entities should soft-delete via `archived_at`; do not add hard-delete
  endpoints for core CRM data.
- Human-curated CRM fields remain source of truth.
- Ritchie governance is strictly binary:
  - `authorized`: execute directly, audit, idempotent.
  - `blocked`: reject and log.
- Do not build proposals, approval queues, approve/reject emails, or per-change
  human review workflows for Ritchie.
- Ritchie must use the scoped API/MCP surface only; no direct DB/filesystem
  access.
- Authenticated human users have equal v1 page/API access unless an endpoint is
  explicitly agent-only.
- Frontend domain types must be generated from FastAPI OpenAPI via
  `openapi-typescript`; do not hand-write TypeScript mirrors of Pydantic schemas.

## Remaining Backend Plan

### Immediate cleanup before feature work

Fix the two Alembic heads described above.

### Agent 09: Gmail Ingestion

Brief: `.agents/09_GMAIL_INGESTION.md`

Can run now because dependencies are complete:

- Agent 02 models/migrations.
- Agent 04 core CRM API.
- Agent 07 document/storage abstraction.

Scope:

- `backend/app/api/routes/email.py`
- `backend/app/services/gmail_ingestion_service.py`
- `backend/app/workers/jobs/gmail_jobs.py`
- `backend/app/repositories/interactions.py`
- Email/interaction schemas only if needed.
- Gmail ingestion tests.

Key requirements:

- CRM receives notifications from kernelbot; do not implement Gmail API/IMAP.
- Raw forwarded message is always stored before parsing.
- Parse original sender, recipient, date, subject, content.
- Parse failures and match failures go to review; never silently drop emails.
- Deterministic matching before AI/fuzzy matching.
- Matched emails become interactions with provenance.
- Capture attachment metadata; store small attachments via storage abstraction.
- Founder/company reply should call Agent 05 pipeline service to move contacted
  companies to `review_needed`; do not reimplement pipeline transition logic.
- Slow work goes to workers.

### Agent 10: Ritchie Agent Integration

Brief: `.agents/10_RITCHIE_AGENT.md`

Can run now because dependencies are complete:

- Agent 03 auth/users/permissions.
- Agent 04 core CRM API.
- Agent 05 pipeline/diligence.
- Agent 07 documents/tasks/notifications.
- Agent 08 search/analytics.

Scope:

- `backend/app/api/routes/agent.py`
- `backend/app/agent/`
- `backend/app/services/agent_service.py`
- `backend/app/services/agent_policy_service.py`
- AI audit paths in `backend/app/services/audit_service.py`
- `backend/app/core/idempotency.py`
- `backend/app/repositories/agent.py`
- `backend/app/integrations/ritchie_client.py`
- `backend/app/workers/jobs/agent_jobs.py`
- Agent tests and fixtures.

Key requirements:

- Typed tool definitions with JSON Schema.
- Runtime binary authorization policy using `agent_policy` model.
- Sensitive defaults blocked:
  - investment amount
  - valuation
  - ownership
  - deal stage/status
  - legal terms
  - investment recommendation
  - portfolio marks
  - rubric scores
- Authorized writes record AI audit intent as `pending` before canonical write,
  then `committed` or `failed`.
- Blocked calls never write and log `policy_blocked` agent event.
- Every write carries idempotency key.
- `/agent/context` uses Agent 08 search service.
- Streamable HTTP MCP surface; SSE is deprecated.
- Agent failures should retry/backoff and never block user-facing workflows.

### Parallelization recommendation

Agents 09 and 10 can run in parallel worktrees now, but they may both touch:

- `backend/app/api/router.py`
- `backend/app/workers/celery_app.py`
- Possibly `backend/app/repositories/interactions.py`
- Possibly audit-related services

Use worktrees and merge in a controlled order:

```bash
git worktree add ../1829-agent-09 -b agent/09-gmail-ingestion v1
git worktree add ../1829-agent-10 -b agent/10-ritchie-agent v1
```

After each agent commits:

1. Merge Agent 09 into `v1` or Agent 10 into `v1`.
2. Resolve expected router/Celery conflicts by keeping both route/job
   registrations.
3. Rebase or merge the second branch onto updated `v1`.
4. Run full backend verification.

### Agent 11: Backend Review And Hardening

Brief: `.agents/11_BACKEND_REVIEW_HARDENING.md`

Run only after Agents 09 and 10 are merged.

Goals:

- Fix integration bugs.
- Verify migration path, including Alembic heads.
- Strengthen integration tests.
- Confirm no Ritchie proposal/approval remnants exist.
- Confirm every create/update/archive path audits correctly.
- Confirm Ritchie key is scoped to agent routes only.
- Confirm backup script works and restore path is viable.
- Stabilize API contracts for frontend.

## Frontend Status And Plan

No frontend implementation has started.

Frontend begins after backend is stable enough for API contracts, ideally after
Agent 11:

1. Agent 20: frontend foundation.
2. Agents 21 and 22 in parallel:
   - CRM workflows.
   - Imports/agent/portfolio pages.
3. Agent 23: frontend polish.

Agent 20 brief:

- `frontend/`
- Vite React TypeScript app.
- shadcn/ui and Tailwind.
- React Router.
- App shell/sidebar.
- API client and auth hook.
- TanStack Query.
- Protected route/session handling.
- OpenAPI type generation via `openapi-typescript`.
- Frontend lint/typecheck/test in CI.

Do not begin frontend by hand-writing domain types. Generate from the FastAPI
OpenAPI spec.

## Worktree Cleanup Done

Codex created and later pruned these worktrees:

```text
../1829-agent-04
../1829-agent-05
../1829-agent-06
../1829-agent-07
../1829-agent-08
```

Only the main `1829-Ventures` checkout remains.

## Final Notes For Gemini

- Work from `v1`.
- Start by fixing the Alembic multiple-head issue.
- Then run Agents 09 and 10, preferably in parallel worktrees if tooling allows.
- Merge back into `v1`, not `main`.
- Keep commits scoped and include the repo convention:

```text
Co-Authored-By: Gemini <gemini@google.com>
```

- Run the backend gate after integration:

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/ruff format --check app tests scripts
DEBUG=false .venv/bin/mypy
DEBUG=false .venv/bin/python -m pytest -q
```

- Do not push unless the user asks.
