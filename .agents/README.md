# 1829 Ventures Codex Agent Assignments

This folder contains mission briefs for running multiple Codex agents against the 1829 Ventures CRM project.

The work should happen in two major waves:

1. Backend first: API foundation, data model, migrations, services, workers, integrations, tests.
2. Frontend second: React/Vite app shell, API client, pages, workflows, and polish.

Each agent should work from its own branch or git worktree. Do not run multiple agents in the same working tree if they may edit overlapping files.

## Required Reading For Every Agent

Before editing files, each agent should read:

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `CONTRIBUTING.md` (code standards: ruff, mypy, ESLint, Prettier, architecture boundaries)
- This `.agents/README.md`
- The specific task brief assigned to that agent

## Operating Rules

- Stay inside the assigned scope.
- Do not make unrelated refactors.
- Do not rewrite planning docs unless the task explicitly says to.
- Prefer small, testable vertical slices.
- Add or update tests for the behavior being implemented.
- Run `ruff` and `mypy` on touched backend code, and ESLint/`tsc` on touched frontend code, before declaring done. CI (`.github/workflows/ci.yml`) runs the same checks and must pass.
- Track code coverage for implemented areas. Use `coverage.py` through `pytest-cov` for backend Python coverage, and Vitest coverage with V8/Istanbul for frontend TypeScript coverage.
- Preserve the route -> service -> repository -> model boundary.
- Keep slow work in workers, not request handlers.
- Ritchie writes are governed by a strictly binary runtime authorization policy: every tool/field is either `authorized` (executes directly, fully audited, idempotent) or `blocked` (rejected and logged as `policy_blocked` until a human updates the policy). There is no proposal or per-change approval workflow — do not build one.
- Every database change (create, update, archive) is audited with actor, timestamp, and old/new values, regardless of actor type.
- Core entities are soft-deleted via `archived_at` — never hard-deleted.
- Human-curated CRM fields remain the source of truth.
- Frontend domain types are generated from the FastAPI OpenAPI spec via `openapi-typescript` — never hand-write TypeScript mirrors of Pydantic schemas.

## Branch And Worktree Pattern

Recommended branch names:

```text
agent/01-backend-foundation
agent/02-models-migrations
agent/03-auth-users-permissions
agent/04-core-crm-api
agent/05-pipeline-diligence
agent/06-dealroom-imports
agent/07-documents-tasks-notifications
agent/08-search-analytics
agent/09-gmail-ingestion
agent/10-ritchie-agent
agent/11-backend-review-hardening
agent/20-frontend-foundation
agent/21-frontend-crm-workflows
agent/22-frontend-imports-agent-portfolio
agent/23-frontend-polish
```

Recommended worktree pattern:

```bash
git worktree add ../1829-agent-01 agent/01-backend-foundation
git worktree add ../1829-agent-02 agent/02-models-migrations
```

Only create a new worktree after creating the matching branch.

## Backend-First Sequence

Strictly sequential foundation:

1. `01_BACKEND_FOUNDATION.md`
2. `02_MODELS_MIGRATIONS.md`
3. `03_AUTH_USERS_PERMISSIONS.md`
4. `04_CORE_CRM_API.md`

After Agent 04 merges, these can run **in parallel** (disjoint file scopes):

- `05_PIPELINE_DILIGENCE.md`
- `06_DEALROOM_IMPORTS.md`
- `07_DOCUMENTS_TASKS_NOTIFICATIONS.md`

Then:

- `08_SEARCH_ANALYTICS.md` (after 05)
- `09_GMAIL_INGESTION.md` (after 04 and 07)
- `10_RITCHIE_AGENT.md` (after 03, 04, 05, 07, 08)

Finally:

- `11_BACKEND_REVIEW_HARDENING.md` (after all of the above)

## Frontend Sequence

Begin frontend work only after the backend has stable API contracts or documented mock contracts.

1. `20_FRONTEND_FOUNDATION.md`
2. `21_FRONTEND_CRM_WORKFLOWS.md` and `22_FRONTEND_IMPORTS_AGENT_PORTFOLIO.md` (parallel — disjoint pages/components)
3. `23_FRONTEND_POLISH.md`

## Shared Files That Need A Single Owner

Be careful with these files because many agents may need to touch them:

```text
docker-compose.yml
docker-compose.prod.yml
README.md
.github/workflows/ci.yml
backend/app/main.py
backend/app/api/router.py
backend/app/models/__init__.py
backend/alembic/versions/
frontend/src/router.tsx
frontend/src/api/client.ts
frontend/src/types/ (generated — regenerate, never hand-edit)
```

If two agents need the same file, merge one branch first and have the second agent rebase or adapt.

Alembic migrations are append-only and conflict-prone: each agent that adds a migration must rebase on the latest merged head and re-stamp `down_revision` before merging.

## Definition Of Done For Any Agent

- The assigned feature exists and matches the plan.
- Relevant tests are added or updated, and pass.
- `ruff` and `mypy` pass on touched backend code; ESLint and `tsc` pass on touched frontend code.
- New environment variables are reflected in `.env.example`.
- New commands are reflected in `README.md` only if they are user-facing.
- No unrelated files are reformatted or rewritten.
