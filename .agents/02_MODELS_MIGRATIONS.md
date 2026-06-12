# Agent 02: Models And Migrations

## Goal

Implement the SQLAlchemy data model and Alembic migrations for the v1 CRM.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `01_BACKEND_FOUNDATION.md`

## May Edit

- `backend/app/models/`
- `backend/app/schemas/`
- `backend/app/core/constants.py`
- `backend/alembic/versions/`
- `backend/scripts/seed_funds.py`
- `backend/tests/unit/`
- `backend/tests/integration/`

## Avoid

- Implementing route handlers beyond what tests need.
- Implementing full services.
- Frontend.
- Ritchie tool execution behavior.

## Expected Output

Models and schemas for:

- Users
- Companies
- People
- Affiliations
- Company contacts
- Interactions
- Deals
- Rubrics
- Diligence checklist items
- Deal statuses
- Funds
- Investments
- Portfolio metrics
- Documents
- Tasks
- Tags
- Import batches
- Import rows
- Human audit log
- AI audit log
- Agent event log
- Agent policy (runtime authorization: tool/field, authorized or blocked, updated_by/at)
- Notifications

Cross-cutting model requirements:

- Soft delete: core entities carry `archived_at` on the shared base — no hard deletes.
- Every create/update/archive must be auditable with actor, timestamp, and old/new values; the audit log models must support this for all actor types (human, import, system, Ritchie).
- There is no agent proposal model — Ritchie governance is the binary `agent_policy` table.

## Tests To Add Or Run

- Migration creation and rollback smoke test if infrastructure exists.
- Model relationship tests for key entities.
- Fund seeding test for Beta and Fund I if practical.

## Definition Of Done

- All planned model files exist.
- Alembic migration creates the tables and indexes needed for v1.
- PostGIS and pgvector requirements are represented where needed.
- Configurable deal statuses are modeled in the database, not hardcoded as enum-only logic.
