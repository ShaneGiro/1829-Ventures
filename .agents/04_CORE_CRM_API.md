# Agent 04: Core CRM API

## Goal

Implement core CRUD and service behavior for companies, people, contacts, affiliations, interactions, funds, investments, portfolio metrics, tags, and documents metadata.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `01_BACKEND_FOUNDATION.md`
- `02_MODELS_MIGRATIONS.md`
- `03_AUTH_USERS_PERMISSIONS.md`

## May Edit

- `backend/app/api/routes/companies.py`
- `backend/app/api/routes/people.py`
- `backend/app/api/routes/interactions.py`
- `backend/app/api/routes/investments.py`
- `backend/app/api/routes/portfolio_metrics.py`
- `backend/app/api/routes/documents.py`
- `backend/app/services/company_service.py`
- `backend/app/services/document_service.py`
- `backend/app/services/audit_service.py` (human/system audit paths; AI audit paths belong to Agent 10)
- `backend/app/core/audit.py`
- Related repositories and schemas.
- Related tests.

## Avoid

- Pipeline/diligence transition rules owned by Agent 05.
- Dealroom import behavior owned by Agent 06.
- Notification sending owned by Agent 07.
- Frontend.

## Expected Output

- Company CRUD with minimal-create support.
- Company completeness calculation for v1 fields.
- People and company contact workflows.
- RIT affiliation CRUD.
- Interactions CRUD and company/person/deal timeline support.
- Funds and investments CRUD.
- Portfolio metric inputs.
- Document metadata and presigned-upload service boundary.
- Manual-field source-of-truth behavior represented in services where applicable.
- Audit logging wired into every create/update/archive path: actor, timestamp, old value, new value.
- Deletion is soft-delete (`archived_at`) on all core entities; no hard-delete endpoints.

## Tests To Add Or Run

- Company CRUD tests.
- Completeness tests.
- People/contact relationship tests.
- Investment/fund relationship tests.
- Document metadata tests.

## Definition Of Done

- Core CRM data can be created, read, updated, and linked through API services.
- Route handlers remain thin and delegate business behavior to services.
