# Agent 01: Backend Foundation

## Goal

Create the backend foundation for the CRM: FastAPI app, project config, database session, Alembic, Docker wiring, worker bootstrapping, and basic health checks.

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
- `docker-compose.yml`
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
- SQLAlchemy engine/session setup exists.
- Alembic is initialized and can see model metadata.
- Redis/Celery worker can boot.
- Docker Compose starts API, Postgres/PostGIS/pgvector, Redis, MinIO, and worker.
- Basic backend test setup exists.

## Tests To Add Or Run

- Add a smoke test for app startup and health endpoint.
- Add a DB session smoke test if practical.

## Definition Of Done

- `backend/app/main.py` creates a working FastAPI app.
- `backend/app/core/config.py`, `database.py`, `dependencies.py`, `security.py`, `exceptions.py`, and `logging.py` exist.
- Docker and local commands are documented enough for the next backend agents.
- No business workflows are implemented in this task.
