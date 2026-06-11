# Agent 08: Search And Analytics

## Goal

Implement keyword search, semantic search infrastructure, embedding jobs, and v1 analytics endpoints.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `02_MODELS_MIGRATIONS.md`
- `04_CORE_CRM_API.md`
- `05_PIPELINE_DILIGENCE.md`

## May Edit

- `backend/app/api/routes/analytics.py`
- `backend/app/services/search_service.py`
- `backend/app/services/analytics_service.py`
- `backend/app/repositories/analytics.py`
- `backend/app/integrations/embeddings.py`
- `backend/app/workers/jobs/embedding_jobs.py`
- `backend/app/workers/jobs/analytics_jobs.py`
- Related model indexes/migrations if needed.
- Search and analytics tests.

## Avoid

- Frontend dashboards.
- Ritchie tool execution, except shared context retrieval contracts if coordinated with Agent 09.

## Expected Output

- Keyword search uses Postgres full-text search.
- Semantic search uses pgvector.
- Embeddings are generated asynchronously.
- `/agent/context` retrieval needs can be supported by the search service.
- Analytics endpoints cover pipeline, portfolio, source, sector, interaction cadence, thesis fit, and agent activity where data exists.

## Tests To Add Or Run

- Search service tests.
- Analytics endpoint tests.
- Embedding job tests with mocked model.

## Definition Of Done

- Search and analytics do not block ordinary writes.
- Heavy work is delegated to workers.
- Embedding model usage is local and configurable.
