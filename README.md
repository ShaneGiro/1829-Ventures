# 1829 Ventures CRM

Internal CRM and operating system for 1829 Ventures. The current codebase includes a FastAPI backend, Postgres/PostGIS/pgvector data model, Redis/Celery worker, MinIO document storage, and a React/Vite frontend for CRM workflows.

## What Is Implemented

- Google OAuth/session-based auth scaffolding with protected frontend routes.
- Company CRM, people/contacts, RIT affiliations, interactions, documents, tasks, and deal pipeline APIs.
- Screening rubric and company completeness tracking.
- Dealroom CSV import upload, preview, dedupe/conflict status, and commit flow.
- Gmail ingestion and fuzzy company matching backend plumbing.
- Portfolio funds, investments, and portfolio summary APIs.
- Ritchie agent policy, typed tool, activity/audit, and webhook integration surfaces.
- React frontend with dashboard, companies, people, pipeline, tasks, imports, portfolio, and Ritchie pages.
- Local Docker stack for Postgres, Redis, MinIO, FastAPI, and Celery.

## Tech Stack

- Backend: FastAPI, SQLAlchemy 2.x, Pydantic, Alembic, Celery.
- Database: Postgres 16 with PostGIS and pgvector.
- Storage: MinIO locally through an S3-compatible interface.
- Frontend: React 18, Vite, TypeScript, TanStack Query, Tailwind CSS, lucide-react.
- Tooling: Ruff, mypy, pytest/coverage, ESLint, Vitest.

## Prerequisites

- Docker Desktop with Compose v2.
- Python 3.12.
- Node.js 20+ and npm.

## Admin: Run From Scratch

Use this section when setting up the app on a new machine or after cloning the repository fresh.

### 1. Install Required Software

Install these before running any project commands:

- Docker Desktop with Docker Compose v2.
- Python 3.12.
- Node.js 20 or newer, which includes `npm`.

Verify the required tools from the repository root:

```bash
make check
```

If `make check` fails, install the missing tool and rerun it before continuing.

### 2. Create Google OAuth Credentials

The local app uses Google OAuth. In Google Cloud Console:

1. Open the Google Cloud project for this app.
2. Go to `APIs & Services` -> `Credentials`.
3. Create or open a `Web application` OAuth 2.0 Client ID.
4. Add this exact authorized redirect URI:

```text
http://localhost:8000/api/auth/callback
```

5. Save the client.
6. Copy the OAuth client ID and client secret for the `.env` file.

If this redirect URI is missing or different, Google login fails with:

```text
Error 400: redirect_uri_mismatch
```

### 3. Create Local Environment File

From the repository root:

```bash
cp .env.example .env
```

Edit `.env` and set these values:

```env
DEBUG=true
API_V1_PREFIX=/api
FRONTEND_URL=http://localhost:5173

GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

JWT_SECRET=replace-with-a-long-random-string
ALLOWED_EMAIL_DOMAINS=g.rit.edu,rit.edu

DATABASE_URL=postgresql://crm:crm@localhost:5432/crm
POSTGRES_USER=crm
POSTGRES_PASSWORD=crm
POSTGRES_DB=crm
POSTGRES_PORT=5432

REDIS_URL=redis://localhost:6379/0

S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_DOCUMENTS=crm-documents
S3_REGION=us-east-1

CORS_ORIGINS=http://localhost:5173
```

Optional values can remain empty during local development:

```env
AGENT_API_KEY=
RITCHIE_WEBHOOK_URL=
SENDGRID_API_KEY=
```

Do not commit `.env`.

### 4. Install Project Dependencies

From the repository root:

```bash
make setup
```

This command:

- Creates `.env` from `.env.example` if `.env` does not already exist.
- Creates `backend/.venv`.
- Installs the CPU-only PyTorch build first.
- Installs backend Python dependencies.
- Installs frontend npm dependencies if `frontend/node_modules` is missing.

Manual equivalent:

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt

cd ../frontend
npm ci
```

### 5. Start Docker Services

From the repository root:

```bash
make up-build
```

This builds and starts:

- Postgres/PostGIS/pgvector on `localhost:5432`.
- Redis on `localhost:6379`.
- MinIO on `localhost:9000`.
- MinIO console on `localhost:9001`.
- FastAPI backend on `localhost:8000`.
- Celery worker.

Check service status:

```bash
make ps
```

Tail logs if anything fails:

```bash
make logs
make logs-api
make logs-worker
```

### 6. Run Database Migrations

The API container runs `alembic upgrade head` on startup, but admins can run migrations explicitly:

```bash
make migrate
```

Verify the app tables exist:

```bash
docker compose exec postgres psql -U crm -d crm -c "\dt"
```

You should see tables such as `users`, `companies`, `people`, `deals`, `tasks`, and `documents`.

If a fresh local database was accidentally stamped at Alembic head without tables, reset only the local development schema with:

```bash
docker compose exec api alembic stamp base
docker compose exec api alembic upgrade head
```

Only use that reset on a disposable local database.

### 7. Start The Frontend

Open a second terminal and run:

```bash
make frontend-dev
```

The frontend starts at:

```text
http://localhost:5173
```

Vite proxies `/api` requests to the backend at:

```text
http://localhost:8000
```

### 8. Log In

Open:

```text
http://localhost:5173/login
```

Click `Continue with Google`.

Expected behavior:

1. Browser redirects to Google.
2. Google redirects back to `http://localhost:8000/api/auth/callback`.
3. The backend sets the session cookie.
4. The backend redirects to `http://localhost:5173`.
5. The frontend loads the authenticated app.

Do not start from `http://localhost:5173/api/auth/login`; use `/login`.

### 9. Verify The App

Useful URLs:

- Frontend: `http://localhost:5173`
- Login page: `http://localhost:5173/login`
- API health: `http://localhost:8000/api/health`
- API docs: `http://localhost:8000/api/docs`
- API OpenAPI JSON: `http://localhost:8000/api/openapi.json`
- MinIO console: `http://localhost:9001`

Run checks:

```bash
make frontend-check
make backend-check
```

### 10. Stop The App

Stop the frontend with `Ctrl+C` in the Vite terminal.

Stop Docker services:

```bash
make down
```

### Common Admin Fixes

Rebuild backend images after changing backend dependencies:

```bash
make up-build
```

Restart only the API container:

```bash
docker compose restart api
```

Check API logs:

```bash
make logs-api
```

Check the current Alembic revision:

```bash
docker compose exec api alembic current
```

Check database tables:

```bash
docker compose exec postgres psql -U crm -d crm -c "\dt"
```

Remove local frontend build artifacts:

```bash
make clean
```

## Environment Setup

From the repository root:

```bash
make setup
```

`make setup` creates `.env` if needed, creates the backend virtual environment, installs backend Python dependencies, and installs frontend npm dependencies.

Manual equivalent:

```bash
cp .env.example .env
cd backend
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
cd ../frontend
npm ci
```

The checked-in `.env.example` is configured for local development. At minimum, set real values in `.env` for these before using OAuth or agent integrations:

- `JWT_SECRET`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `AGENT_API_KEY`
- `RITCHIE_WEBHOOK_URL` if outbound Ritchie event fanout is needed

## Run With Docker Backend + Local Frontend

This is the default development path. Docker runs the backend dependencies, API, and worker. Vite runs the frontend locally and proxies `/api` to `http://localhost:8000`.

Start the backend stack and frontend dev server:

```bash
make dev
```

`make dev` runs `make up`, ensures frontend dependencies are present, then starts Vite.

If you want separate terminals, start the backend stack:

```bash
make up
```

Then run the frontend:

```bash
make frontend-dev
```

Manual equivalent:

```bash
docker compose up -d
cd frontend
npm run dev
```

Open:

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/api/docs`
- API OpenAPI JSON: `http://localhost:8000/api/openapi.json`
- MinIO console: `http://localhost:9001`

Stop the Docker stack:

```bash
make down
```

Manual equivalent:

```bash
docker compose down
```

## Run Backend Locally Without Docker API Container

Use this when you want the API process directly on your machine. You still need Postgres, Redis, and MinIO running.

Start infrastructure, install backend dependencies, run migrations, and start the API:

```bash
make backend-dev
```

From another terminal, start the local worker if background jobs are needed:

```bash
make backend-worker
```

Manual equivalent:

```bash
docker compose up -d postgres redis minio minio-init
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

Manual worker command:

```bash
cd backend
source .venv/bin/activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

## Frontend Commands

Preferred Makefile commands from the repository root:

```bash
make frontend-dev
make frontend-lint
make frontend-typecheck
make frontend-test
make frontend-build
make frontend-preview
make frontend-check
```

Manual equivalents from `frontend/`:

```bash
npm ci
npm run dev
npm run lint
npm run typecheck
npm test
npm run build
npm run preview
```

Regenerate OpenAPI TypeScript types after backend API schema changes:

```bash
make frontend-gen-api
```

`frontend/vite.config.ts` runs the dev server on port `5173` and proxies `/api` to `http://localhost:8000`.

## Backend Commands

Preferred Makefile commands from the repository root:

```bash
make migrate
make revision m="message"
make lint
make format
make typecheck
make test
make test-cov
make backend-check
make logs
make logs-api
make logs-worker
make shell
```

Manual equivalents from `backend/` with the virtual environment activated:

```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
ruff check .
ruff format .
mypy
pytest
pytest --cov=app --cov-report=term-missing
```

## Makefile Shortcuts

```bash
make help
make check
make setup
make dev
make up
make up-build
make up-infra
make down
make restart
make ps
make logs
make frontend-check
make backend-check
make clean
```

## Docker Services

`docker-compose.yml` defines:

- `postgres`: Postgres 16 with PostGIS and pgvector.
- `redis`: broker/rate-limit store.
- `minio`: local S3-compatible object storage.
- `minio-init`: one-shot bucket setup.
- `api`: FastAPI on `http://localhost:8000`.
- `worker`: Celery worker.

The frontend is not currently a Compose service in the development stack; run it with `npm run dev` from `frontend/`.

## Project Layout

```text
backend/      FastAPI app, services, repositories, workers, Alembic, tests
frontend/     React/Vite app, API clients, pages, components, tests
docker/       Local Postgres and MinIO support files
nginx/        Production SPA/API reverse-proxy config stub
planning/     Implementation notes and model handoff docs
.agents/      Agent task briefs
```

## Planning Docs

- `DESIGN_DOC.md`: current design documentation.
- `planning/FILE_STRUCTURE.md`: planned file structure.
- `planning/APP_WORKFLOW_AND_FILES.md`: app workflow and file guide.
- `planning/MODEL_COMMS.md`: cross-model implementation handoff notes.

## Notes

- Do not commit `.env`.
- Install CPU-only PyTorch before `pip install -r backend/requirements.txt`; otherwise pip may pull an unnecessary CUDA build.
- Production Compose/nginx wiring is still a stub in `docker-compose.prod.yml`; v1 development uses Docker for backend services and Vite for the frontend.
