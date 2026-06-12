# Agent 05: Pipeline And Diligence

## Goal

Implement relationship/investment status workflows, review-needed triage, configurable deal statuses, diligence checklist behavior, and screening rubric scoring.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `planning/1829 Ventures Screening Rubric.pdf`
- `.agents/README.md`

## Depends On

- `02_MODELS_MIGRATIONS.md`
- `04_CORE_CRM_API.md`

## May Edit

- `backend/app/api/routes/deals.py`
- `backend/app/api/routes/deal_statuses.py`
- `backend/app/services/deal_service.py`
- `backend/app/services/pipeline_service.py`
- `backend/app/services/diligence_service.py`
- `backend/app/repositories/deals.py`
- `backend/app/repositories/deal_statuses.py`
- Deal, rubric, diligence, and pipeline tests.

## Avoid

- Dealroom import.
- Ritchie proposal drafting.
- Frontend.

## Expected Output

- Separate relationship status and investment status behavior.
- Review-needed triage outcomes: start investment review, monitor, pass.
- Pass requires reason tags.
- Monitor requires next-check date and creates/reminds later through task hooks.
- Start-review creates first investment opportunity, initializes diligence checklist, and attaches screening rubric.
- Configurable pipeline stages are DB-backed.
- Rubric stores knockout gates and 15 sub-scores.
- Composite score and thresholds are computed consistently.

## Tests To Add Or Run

- `test_pipeline_service.py`
- `test_diligence_service.py`
- API integration tests for triage and rubric updates.

## Definition Of Done

- Pipeline logic is centralized in services.
- Rubric scoring matches the planned weights and thresholds.
- Configurable statuses are not hardcoded as the only source of truth.
