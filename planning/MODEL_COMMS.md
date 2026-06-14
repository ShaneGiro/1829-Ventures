# Model-to-Model Handoff (MODEL_COMMS)

Running log for AI agents handing off work on the 1829 Ventures CRM build.
Newest handoff at the top. Read this **plus** `PLAN_v1.md`, `FILE_STRUCTURE.md`,
`APP_WORKFLOW_AND_FILES.md`, `CONTRIBUTING.md`, and `.agents/README.md` before
editing.

---

## HANDOFF 1 — Claude (Sonnet/Opus) → Codex 5.5 — 2026-06-14

### TL;DR
Agent 01 (Backend Foundation) and Agent 02 (Models & Migrations) are **done,
committed, and verified against real Postgres**. You are picking up at **Agent 03
(Auth, Users, Permissions)**. The build sequence is strictly sequential through
Agent 04; do not parallelize before 04 merges.

### Where the code lives
- Repo root: `/Users/shanegirolamo/Downloads/1829 Ventures Software/1829-Ventures/`
- It IS a git repo. kernelbot lives in a SEPARATE repo at
  `/Users/shanegirolamo/Downloads/1829 Ventures Software/kernelbot_rit/` — do not
  merge it in.

### Git state
Branches (each agent on its own branch, per `.agents/README.md`):
```
v1                              <- base branch the work started from
agent/01-backend-foundation     <- commit e992d61
agent/02-models-migrations      <- commit 9812eb1 (branched off 01)  <-- HEAD is here
```
Commits so far:
- `9812eb1` Agent 02: data model, schemas, and initial migration
- `e992d61` Agent 01: backend foundation

Nothing has been pushed or merged to `v1`/`main` yet. Recommended: open PRs
01→v1, 02→v1 (or merge locally) in order, OR just keep stacking branches. Create
`agent/03-auth-users-permissions` off `agent/02-models-migrations`.

> NOTE: `main` and `v1` had diverged earlier; `git pull` needs an explicit
> `--no-rebase`/`--rebase`/`--ff-only`. Not blocking local work.

### Environment realities (IMPORTANT)
- **Local Python is 3.11.8** (anaconda env `Test_3_11_8`), but the project targets
  **3.12** (`pyproject.toml`, CI). All code is written to run on 3.11 too (uses
  `datetime.UTC`, `StrEnum`, `X | None`). **Do NOT introduce PEP 695 syntax**
  (`class Foo[T]`, `type X = ...`) — it breaks local 3.11 runs. Ruff rules UP046/
  UP047 are already disabled for this reason.
- **No virtualenv is committed.** I created a throwaway `backend/.venv` to run
  tests, then deleted it. Recreate one to work locally (see "How to run" below).
- **Docker Desktop must be running** for DB-backed work. On macOS: `open -a Docker`
  then wait for `docker ps` to succeed. It was slow to start (~minutes) on this
  machine.
- `requirements.txt` includes torch + sentence-transformers (heavy, ~for Agent 08
  embeddings). For fast iteration I installed only the lightweight subset into the
  venv and skipped torch. Full `pip install -r requirements.txt` works but pulls
  torch CPU wheel first (see note at top of requirements.txt).

### How to run / test locally (what I actually did)
```bash
cd "/Users/shanegirolamo/Downloads/1829 Ventures Software/1829-Ventures"
cp .env.example .env                      # if not present
docker compose up -d postgres redis       # postgres image is BUILT (has pgvector)

cd backend
python3 -m venv .venv
.venv/bin/pip install -U pip
# lightweight subset (skip torch unless you need embeddings):
.venv/bin/pip install "fastapi>=0.115" "uvicorn[standard]" "pydantic>=2.10" \
  "pydantic-settings>=2.7" "sqlalchemy>=2.0.36" asyncpg psycopg2-binary \
  "pyjwt[crypto]" "redis>=5.2" "celery>=5.4" httpx pytest pytest-asyncio \
  pytest-cov "alembic>=1.14" geoalchemy2 pgvector email-validator ruff mypy authlib

export DATABASE_URL="postgresql://crm:crm@localhost:5432/crm" JWT_SECRET="test"

# migrations (run alembic with venv/bin on PATH so the ruff post-write hook works):
PATH="$PWD/.venv/bin:$PATH" alembic upgrade head
.venv/bin/python -m scripts.seed_funds

# quality gate (all currently green):
.venv/bin/ruff check . && .venv/bin/ruff format --check app tests scripts
.venv/bin/mypy
.venv/bin/python -m pytest -q          # 16 passed
# DB-free only:  pytest -m "not integration"
```
Settings load `.env` from the CWD. When running from `backend/`, either export the
env vars (as above) or create a `backend/.env`. The repo `.env` is at root.

### What Agent 01 delivered (commit e992d61)
FastAPI + Celery scaffold. Key files:
- `backend/app/core/config.py` — Pydantic-settings; single `DATABASE_URL` →
  `async_database_url` (asyncpg) + `sync_database_url` (psycopg2) computed props.
  `allowed_domains_list`, `cors_origins_list` helpers. `database_url` is typed
  `str` (NOT PostgresDsn — that broke mypy default assignment).
- `backend/app/core/database.py` — **dual engines**: `async_engine`/
  `AsyncSessionLocal` + `get_async_session` (API); `sync_engine`/
  `SyncSessionLocal` + `get_sync_session` (Celery + Alembic). Workers never use
  async.
- `backend/app/core/security.py` — PyJWT `create_access_token`/
  `decode_access_token`; API-key `generate/hash/verify` (sha256 + hmac compare).
- `backend/app/core/exceptions.py` — `AppError` hierarchy incl. `PolicyBlockedError`
  (used by Agent 10), `PermissionDeniedError`, etc. `main.py` maps these to HTTP.
- `backend/app/core/logging.py` — JSON logging + `request_id_ctx` ContextVar.
- `backend/app/core/dependencies.py` — `DbSession = Annotated[AsyncSession,
  Depends(get_async_session)]`. **Agent 03 adds current-user/permission deps here.**
- `backend/app/api/middleware.py` — `RequestIDMiddleware` + `RateLimitMiddleware`
  (Redis token-bucket, tiers `agent_read` 120/min, `agent_write` 60/min,
  `default` 300/min; fails open). Agent 10 refines tier classification.
- `backend/app/api/router.py` — single `api_router`; **register new sub-routers
  here.** Currently only health.
- `backend/app/api/routes/health.py` — `/api/health`, `/api/health/ready`.
- `backend/app/main.py` — app factory, mounts router at `settings.api_v1_prefix`
  (`/api`), docs at `/api/docs`, OpenAPI at `/api/openapi.json`.
- `backend/app/workers/celery_app.py` — Celery bootstrap, `health.ping` task.
- Infra: `docker-compose.yml` (api, worker, postgres[BUILT], redis, minio,
  minio-init), `docker-compose.prod.yml` (stub), `Makefile`, `.env.example`,
  `.editorconfig`, `.gitignore`, `.github/workflows/ci.yml`,
  `backend/scripts/backup_db.sh`, `docker/postgres/{Dockerfile,init.sql}`,
  `docker/minio/init.sh`.

### What Agent 02 delivered (commit 9812eb1)
**23 models + `company_tags` join (24 tables)** in `backend/app/models/`, all
registered in `models/__init__.py` (Alembic reads it). All use
`base.py` mixins: `UUIDPrimaryKeyMixin`, `TimestampMixin`, `SoftDeleteMixin`
(`archived_at` + `is_archived`).
- CRM: `user`, `company` (PostGIS `location` Geometry POINT 4326 + pgvector
  `embedding` Vector(384) + `field_provenance` JSONB + `imported_unreviewed`),
  `person`, `affiliation`, `company_contact`, `interaction` (pgvector embedding).
- Deals: `deal`, `rubric` (4 `gate_*` knockout booleans + 15 named sub-score
  ints + `composite_score` float — composite computed later by Agent 05's
  diligence service), `diligence_checklist_item`, `deal_status` (configurable,
  DB-backed, `is_system`/`is_terminal`/`sort_order`).
- Fund: `fund`, `investment`, `portfolio_metric`.
- Workflow: `document`, `task` (owner nullable = shared queue; `created_by_type`
  ActorType; `watcher_ids` JSONB list), `tag` (`company_tags` Table + TagKind
  user/system/pass_reason).
- Imports: `import_batch`, `import_row` (raw_data + field_provenance + conflicts
  JSONB).
- Governance: `audit_log` (actor_type/old/new/reason), `ai_audit_log` (Ritchie
  intent→committed/failed, `idempotency_key` UNIQUE), `agent_event_log` (incl.
  `policy_blocked`, AgentEventStatus), `agent_policy` (**binary** PolicyState
  authorized/blocked, unique on (tool, field_name)), `notification`.
- **There is NO proposal/approval model — do not add one.** Governance is the
  binary `agent_policy` table only.

Schemas in `backend/app/schemas/` — Create/Read/Update per entity on a shared
`common.py` base (`ORMModel`, `TimestampedRead`, `SoftDeleteRead`,
`PaginatedResponse[T]`). Downstream agents extend with route-specific models.

`backend/app/core/constants.py` — enums & maps you will reuse:
`RelationshipStatus`, `InvestmentStatus`, `Role`, `ActorType`, `InteractionType`,
`TaskStatus/Priority`, `TagKind`, `DocumentSource`, `NotificationChannel`,
`ImportStatus`, `ImportRowStatus`, `FundStatus`, `DiligenceItemStatus`,
`PolicyState`, `AgentEventStatus`, `AiWriteStatus`; `SECTOR_TAXONOMY`,
`SEED_DEAL_STATUSES`, `RUBRIC_CATEGORIES`, `RUBRIC_SUBSCORES` (15),
`RUBRIC_KNOCKOUT_GATES` (4), score thresholds, `COMPANY_COMPLETENESS_FIELDS`,
`DEFAULT_BLOCKED_TOOLS`, `EMBEDDING_DIM = 384`.

Migration: `backend/alembic/versions/4d6ffdeb3a50_initial_schema.py` (creates all
24 tables). `seed_funds.py` seeds Beta, Fund I + 7 pipeline stages (idempotent).

### Migration gotchas already solved (don't re-break these)
1. **Postgres needs PostGIS AND pgvector.** The stock `postgis/postgis:16-3.4`
   image has NO pgvector. `docker/postgres/Dockerfile` extends it and
   `apt-get install postgresql-16-pgvector`. Compose `build:`s it; CI builds+runs
   it as a container (GitHub Actions `services:` can't build images).
2. **`alembic/env.py` has an `include_name` filter** so autogenerate ignores the
   ~37 PostGIS tiger/topology system tables. Without it, autogenerate tries to
   manage them. Keep it.
3. **GeoAlchemy2 auto-creates/drops the `idx_companies_location` GiST index** on
   table create/drop. The explicit `op.create_index`/`op.drop_index` for it were
   REMOVED from the migration (they caused "relation already exists"). If you
   regenerate a migration touching `companies.location`, remove those again.
4. **Autogenerate omits `import geoalchemy2` / `import pgvector.sqlalchemy`** from
   the migration header — add them by hand after generating (there's a reminder
   comment in `env.py`). A `render_item` hook was tried and did NOT work in this
   version combo; don't waste time on it.
5. Verified: upgrade→downgrade→upgrade clean; `alembic check` = "No new upgrade
   operations detected" (no drift).

### Tooling config notes
- `pyproject.toml`: ruff (line 100, E/W/F/I/B/C4/UP/SIM/TID; ignores B008,
  UP046, UP047) with `alembic/versions` excluded from ruff. mypy `strict = true`
  but `disallow_untyped_decorators = false` (Celery `@task` is untyped); missing-
  stub overrides include geoalchemy2, pgvector, celery, authlib, sendgrid,
  sentence_transformers, factory.
- JSONB columns are typed `Mapped[dict[str, Any]]` / `Mapped[list[Any]]` (mypy
  strict requires the args). Follow that pattern for new JSONB columns.
- pytest: `asyncio_mode = auto`, marker `integration` for DB-backed tests.
  `addopts` turns on `--cov`; use `--no-cov` for quick runs.

### YOUR NEXT TASK — Agent 03 (Auth, Users, Permissions)
Read `.agents/03_AUTH_USERS_PERMISSIONS.md`. Branch off `agent/02-models-migrations`.
Deliver (May Edit list is in the brief):
- `integrations/google_oauth.py` — Google OAuth client (authlib is in
  requirements) + profile fetch (People API).
- `services/auth_service.py` — OAuth callback handling, account auto-create on
  first eligible login, JWT issue, agent-key auth. Use `core/security.py` helpers.
- Domain allowlist: eligible RIT Google accounts, esp. `@g.rit.edu`. Config has
  `allowed_domains_list` already. v1 = anyone with eligible domain can log in.
  Structure for future invite-gating but don't build it (mark pending).
- `services/permission_service.py` + `core/permissions.py` — central
  `require_permission(user, action, resource)`; returns True for any authenticated
  human in v1. Add the matching FastAPI deps to `core/dependencies.py`
  (`CurrentUser`, etc.).
- Ritchie scoped API-key auth: only `/agent/*` routes accept the agent key; the
  key rejects all other routes with 403. Enforce at the API layer. The `User`
  model already has `is_agent` + `api_key_hash`.
- `api/routes/auth.py` (login/callback/refresh/logout/me) and `api/routes/users.py`.
  **Register both routers in `api/router.py`.**
- `scripts/rotate_agent_key.py`.
- Tests: domain allowlist (incl. `@g.rit.edu`), permission guard equal-access,
  agent-key accept/reject. JWT stored in httpOnly cookie (see PLAN auth flow).
- Add any new env vars to `.env.example` (GOOGLE_* and AGENT_API_KEY already there).

### Sequence reminder (from .agents/README.md)
01→02→03→04 sequential. After 04: 05/06/07 parallel (use git worktrees if running
concurrently). Then 08 (after 05), 09 (after 04+07), 10 (after 03/04/05/07/08),
11 (after all). Frontend 20→(21+22)→23.

### Non-negotiable design rules (from the plan)
- Ritchie governance is **binary** authorized/blocked. No proposal/approval queue.
- Every create/update/archive is **audited** (actor, ts, old, new) regardless of
  actor (human/import/system/Ritchie). Soft-delete via `archived_at`; never hard
  delete core entities.
- Human-curated fields are source of truth; Ritchie can't overwrite unless the
  field is explicitly `authorized` in the runtime policy.
- Routes = HTTP only; services = business logic/permissions/audit; repositories =
  SQLAlchemy; workers = slow/async; Ritchie talks only via the typed API/MCP.
- Frontend domain types come from OpenAPI codegen — never hand-written.
- MCP transport = Streamable HTTP (SSE deprecated).

### Verification expectations before you commit
Run and pass: `ruff check .`, `ruff format --check`, `mypy`, `pytest` (with
Docker Postgres up for integration tests). Keep CI green. End commit messages with
`Co-Authored-By:` per the repo convention.
