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
- This `.agents/README.md`
- The specific task brief assigned to that agent

## Operating Rules

- Stay inside the assigned scope.
- Do not make unrelated refactors.
- Do not rewrite planning docs unless the task explicitly says to.
- Prefer small, testable vertical slices.
- Add or update tests for the behavior being implemented.
- Preserve the route -> service -> repository -> model boundary.
- Keep slow work in workers, not request handlers.
- Keep Ritchie writes typed, audited, idempotent, and approval-gated where required.
- Human-curated CRM fields remain the source of truth.

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
agent/09-ritchie-agent
agent/10-backend-review-hardening
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

Start with these agents:

1. `01_BACKEND_FOUNDATION.md`
2. `02_MODELS_MIGRATIONS.md`
3. `03_AUTH_USERS_PERMISSIONS.md`

Then continue:

4. `04_CORE_CRM_API.md`
5. `05_PIPELINE_DILIGENCE.md`
6. `06_DEALROOM_IMPORTS.md`
7. `07_DOCUMENTS_TASKS_NOTIFICATIONS.md`
8. `08_SEARCH_ANALYTICS.md`
9. `09_RITCHIE_AGENT.md`
10. `10_BACKEND_REVIEW_HARDENING.md`

## Frontend Sequence

Begin frontend work only after the backend has stable API contracts or documented mock contracts.

1. `20_FRONTEND_FOUNDATION.md`
2. `21_FRONTEND_CRM_WORKFLOWS.md`
3. `22_FRONTEND_IMPORTS_AGENT_PORTFOLIO.md`
4. `23_FRONTEND_POLISH.md`

## Shared Files That Need A Single Owner

Be careful with these files because many agents may need to touch them:

```text
docker-compose.yml
docker-compose.prod.yml
README.md
backend/app/main.py
backend/app/api/router.py
backend/app/models/__init__.py
backend/alembic/versions/
frontend/src/router.tsx
frontend/src/api/client.ts
```

If two agents need the same file, merge one branch first and have the second agent rebase or adapt.

## Definition Of Done For Any Agent

- The assigned feature exists and matches the plan.
- Relevant tests are added or updated.
- Existing tests in the touched area pass, or failures are documented.
- New environment variables are reflected in `.env.example`.
- New commands are reflected in `README.md` only if they are user-facing.
- No unrelated files are reformatted or rewritten.
