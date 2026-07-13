# Backend Review & Hardening (Agent 11)

Historical status after Agents 01–10, verified before frontend integration. See
`planning/V1_3_EXECUTION.md` for the current v1.3 delivery and release gates.

## Historical verification results (all green at that point)
- **Lint/format:** `ruff check .` + `ruff format --check` clean.
- **Types:** `mypy` strict — no issues across 136 source files.
- **Tests:** full suite passes (92 unit + integration), ~65% line coverage.
- **Migrations:** single head (`38f12c67c5ce` at the time). `alembic upgrade head` → `downgrade
  base` → `upgrade head` all succeed against a clean PostGIS+pgvector database.
- **CI** (`.github/workflows/ci.yml`): ruff + mypy + pytest steps match the local
  gate; the Postgres service is the custom PostGIS+pgvector image.

## Checklist confirmation
- Routes stay thin; services own business logic; repositories own SQLAlchemy;
  workers handle slow work (embeddings, imports, notifications, gmail, agent fanout).
- Ritchie's agent key is scoped to `/agent/*` (`CurrentAgent`); human JWTs are
  rejected from agent tool/context routes; agent keys are rejected elsewhere.
- Agent policy is **strictly binary** (`PolicyState.AUTHORIZED|BLOCKED`). No
  proposal/approval workflow exists — the only matches for "proposal/approval" in
  the code are comments affirming its absence.
- Ritchie writes record AI-audit intent (pending → committed/failed), carry an
  idempotency key (unique-constrained), and blocked tools/fields never reach a
  handler (gate runs before any service logic).
- Every create/update/archive is audited (actor, timestamp, old/new). Core
  entities soft-delete via `archived_at`.
- Dealroom import preserves raw rows + per-field provenance; configurable deal
  statuses are DB-backed (`deal_statuses`).
- Gmail ingestion stores the raw message first; parse/match failures land in the
  review queue (`parse_failed` / `unmatched`); fuzzy matches are suggestions only.

## Fix applied
- **Alembic autogenerate drift on raw-SQL indexes.** Agent 08's pgvector HNSW and
  GIN full-text indexes are created via raw SQL and are not on the model metadata,
  so autogenerate emitted spurious `drop_index` ops. Added a
  `process_revision_directives` hook in `alembic/env.py` that strips create/drop
  ops for indexes named `*_embedding_hnsw` / `*_search_fts`. `alembic revision
  --autogenerate` now produces a clean (empty) migration — developers won't
  accidentally drop the search indexes.

## Known limitations (documented, non-blocking)
- `alembic check` still reports the five raw-SQL indexes as "removed". This is an
  alembic limitation: `check` compares metadata directly and does **not** invoke
  `process_revision_directives` or `include_object` for index removal. It does
  **not** affect CI (CI runs ruff/mypy/pytest, not `alembic check`) or runtime —
  the indexes are correctly created by the migrations. Revisit if alembic adds a
  reflection-level exclusion hook for indexes.
- Service tests use fake-session/monkeypatch units (the repo has no async DB
  fixture). Core flows have Postgres-backed integration tests in
  `tests/integration/`; deeper async route-level integration is a future add.

## Contract stability for frontend
The API surface (OpenAPI at `/api/openapi.json`) was stable for Agents 20–23.
Auth: human JWT via httpOnly cookie / bearer; `/agent/*` is agent-key-only.
