# Agent 11: Backend Review And Hardening

## Goal

Review, test, and harden the backend after the first implementation wave.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`
- All prior backend agent briefs.

## Depends On

- Agents 01 through 10.

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
- Ritchie writes are audited and idempotent; blocked tools/fields cannot write under any code path.
- The agent authorization policy is strictly binary (authorized/blocked) — confirm no proposal/approval remnants exist.
- Every create/update/archive is audited with actor, timestamp, and old/new values; core entities soft-delete via `archived_at`.
- Dealroom import preserves raw rows and provenance.
- Gmail ingestion never drops an email: raw message stored, parse/match failures land in the review queue.
- Configurable statuses are database-backed.
- Human-curated fields are not silently overwritten.
- CI (`.github/workflows/ci.yml`) is green: ruff, mypy, pytest with coverage.
- Backup script works: run `backup_db.sh` and restore the dump onto a clean Postgres container.

## Definition Of Done

- Backend is ready for frontend integration.
- Failing tests are either fixed or explicitly documented with rationale.
