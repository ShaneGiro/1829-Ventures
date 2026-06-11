# Agent 06: Dealroom Imports

## Goal

Implement Dealroom CSV upload, parsing, preview, dedupe, conflict review, provenance tracking, and partial commit.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `Dealroom Data (6.10.26).csv`
- `.agents/README.md`

## Depends On

- `02_MODELS_MIGRATIONS.md`
- `04_CORE_CRM_API.md`

## May Edit

- `backend/app/api/routes/imports.py`
- `backend/app/integrations/dealroom_csv.py`
- `backend/app/services/dealroom_import_service.py`
- `backend/app/repositories/imports.py`
- `backend/app/workers/jobs/dealroom_import_jobs.py`
- Import models/schemas if missing fields are discovered.
- Dealroom import tests.

## Avoid

- General company CRUD outside import needs.
- Frontend import UI.
- Ritchie behavior.

## Expected Output

- CSV metadata rows are detected and skipped.
- Header row is detected.
- Semicolon-delimited fields are parsed.
- Parallel arrays for founders and funding rounds are handled.
- Latitude/longitude loads directly into geography fields.
- Dealroom taxonomy maps to 1829 sector taxonomy.
- Preview shows created/matched/skipped/conflict rows.
- Partial commit creates clean records and preserves unresolved rows.
- Imported companies start as `imported_unreviewed`.

## Tests To Add Or Run

- `test_dealroom_csv.py`
- `test_dealroom_import.py`

## Definition Of Done

- The provided Dealroom CSV can be parsed in a test or local command.
- Import preview and commit are separate service steps.
- Import rows preserve raw payload and field provenance.
