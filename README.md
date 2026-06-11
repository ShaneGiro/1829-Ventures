# 1829 Ventures CRM

Internal CRM and operating system for 1829 Ventures.

This app is designed to help the team manage alumni founder relationships, deal flow, diligence, portfolio tracking, tasks, documents, Dealroom imports, Gmail ingestion, analytics, and Ritchie, the AI agent.

## How It Works

The CRM is company-centered. A company record is the primary workspace and connects to people, contacts, affiliations, interactions, deals, diligence, documents, tasks, investments, portfolio metrics, imports, audit history, and Ritchie activity.

The planned runtime architecture is:

```text
React + Vite frontend
  -> nginx
  -> FastAPI backend
  -> service layer
  -> SQLAlchemy repositories
  -> Postgres/PostGIS/pgvector

FastAPI and services also enqueue background work:

Redis queue
  -> Celery workers
  -> Dealroom imports, Gmail processing, embeddings,
     notifications, analytics refreshes, and Ritchie event fanout
```

## Core Workflows

- Google OAuth login for internal users.
- Company CRM records with completeness tracking and source provenance.
- People, contacts, and RIT affiliations.
- Deal pipeline with separate relationship and investment status lanes.
- Review-needed triage for start-review, monitor, or pass decisions.
- Screening rubric and diligence checklist per investment opportunity.
- Funds, investments, ownership inputs, and portfolio metrics.
- Dealroom CSV upload, preview, dedupe, conflict review, and partial commit.
- Gmail forwarding ingestion through Ritchie's inbox and kernelbot.
- Document metadata in Postgres with S3-compatible object storage.
- Tasks, reminders, assignments, daily digests, and proposal notifications.
- Keyword and semantic search using Postgres full-text search and pgvector.
- Ritchie typed tools, trusted writes, approval-required proposals, and full audit logging.

## Architecture Principles

- Routes handle HTTP only.
- Services own business logic and permissions.
- Repositories isolate database queries.
- Workers handle slow or asynchronous jobs.
- Integrations wrap external systems such as Google OAuth, SendGrid, MinIO, Dealroom parsing, embeddings, and kernelbot/Ritchie.
- Human-curated CRM fields remain the source of truth.
- Ritchie can write only through typed, audited, idempotent backend tools.
- Sensitive Ritchie actions require human approval.

## Main Technologies

- Backend: FastAPI, SQLAlchemy 2.x, Pydantic, Alembic.
- Database: Postgres with PostGIS and pgvector.
- Background jobs: Redis plus Celery.
- Storage: MinIO locally, S3-compatible storage later.
- Frontend: React, Vite, TypeScript, TanStack Query, React Hook Form, Zod, shadcn/ui.
- Proxy/deployment: nginx and Docker Compose.

## Planning Docs

- `PLAN v1.md`: product and technical plan.
- `planning/FILE_STRUCTURE.md`: planned file structure.
- `planning/APP_WORKFLOW_AND_FILES.md`: app workflow and file-by-file guide.
- `planning/MODEL_COMMS.md`: notes for cross-model review.

## Current Status

This repository is in planning/scaffolding mode. The current priority is to lock the architecture, file structure, and implementation plan before generating the backend and frontend code.
