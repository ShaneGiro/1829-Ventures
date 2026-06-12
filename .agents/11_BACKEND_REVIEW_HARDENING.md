# Agent 10: Backend Review And Hardening

## Goal

Review, test, and harden the backend after the first implementation wave.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`
- All prior backend agent briefs.

## Depends On

- Agents 01 through 09.

## May Edit

- Backend tests.
- Bug fixes in backend code.
- `.env.example`
- `README.md` if commands changed.
- Migrations only if required to fix schema bugs.

## Avoid

- New feature scope.
- Frontend implementation.
- Large refactors unless required to fix correctness.

## Expected Output

- Backend test suite is coherent.
- Migration path is verified.
- Core workflows have integration coverage.
- Known gaps are documented.
- API contracts are stable enough for frontend agents.

## Review Checklist

- Routes remain thin.
- Services own business logic.
- Repositories own SQLAlchemy queries.
- Workers handle slow work.
- Auth/permissions keep Ritchie's agent key scoped to agent surfaces. Authenticated human users have equal page/API access in v1 unless a route is explicitly agent-only.
- Ritchie writes are audited and idempotent.
- Dealroom import preserves raw rows and provenance.
- Configurable statuses are database-backed.
- Human-curated fields are not silently overwritten.

## Definition Of Done

- Backend is ready for frontend integration.
- Failing tests are either fixed or explicitly documented with rationale.
