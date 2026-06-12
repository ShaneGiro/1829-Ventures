# Agent 01: Backend Foundation

## Goal

Create the backend foundation for the CRM: FastAPI app, project config, database sessions, Alembic, Docker wiring, worker bootstrapping, CI, backups, and basic health checks.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## May Edit

- `backend/Dockerfile`
- `backend/.dockerignore`
- `backend/pyproject.toml`
- `backend/requirements.txt`
- `backend/alembic.ini`
- `backend/alembic/`
- `backend/app/main.py`
- `backend/app/core/`
- `backend/app/api/router.py`
- `backend/app/api/middleware.py`
- `backend/app/workers/celery_app.py`
- `backend/scripts/backup_db.sh`
- `docker-compose.yml`
- `docker/postgres/init.sql`
- `docker/minio/`
- `.github/workflows/ci.yml`
- `.env.example`
- `Makefile`

## Avoid

- Full domain models beyond minimal placeholders needed for app boot.
- Frontend implementation.
- Ritchie tool behavior.
- Dealroom parsing.

## Expected Output

- FastAPI app starts.
- `/health` or equivalent health endpoint works.
- Dual SQLAlchemy engines in `core/database.py`: async (asyncpg) + async session factory for FastAPI request handlers, sync (psycopg2) + sync session factory for Celery workers and Alembic. Workers never use the async engine.
- Alembic is initialized and can see model metadata.
- `docker/postgres/init.sql` enables the `postgis` and `vector` extensions on first container start, before the first migration; MinIO init creates default buckets.
- Redis/Celery worker can boot.
- Docker Compose starts API, Postgres/PostGIS/pgvector, Redis, MinIO, and worker.
- Redis token-bucket rate-limiting middleware skeleton and request ID injection exist in `api/middleware.py` (no external rate-limit library).
- JWT helpers in `core/security.py` use PyJWT (not python-jose).
- `.github/workflows/ci.yml` runs ruff, mypy, and pytest with coverage on every push/PR (frontend steps added later by Agent 20).
- `backend/scripts/backup_db.sh` performs a nightly `pg_dump`: compress, retain 14 days, copy off-VM; wired as a cron or compose service.
- Basic backend test setup exists.

## Tests To Add Or Run

- Add a smoke test for app startup and health endpoint.
- Add a DB session smoke test if practical.

## Definition Of Done

- `backend/app/main.py` creates a working FastAPI app.
- `backend/app/core/config.py`, `database.py`, `dependencies.py`, `security.py`, `exceptions.py`, and `logging.py` exist.
- Docker and local commands are documented enough for the next backend agents.
- No business workflows are implemented in this task.
