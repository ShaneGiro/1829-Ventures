# Agent 21: Frontend CRM Workflows

## Goal

Implement the core CRM frontend workflows: pipeline board, company detail, contacts, interactions, tasks, and documents.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `20_FRONTEND_FOUNDATION.md`
- Stable backend endpoints for companies, people, deals, interactions, tasks, and documents.

## May Edit

- `frontend/src/pages/PipelineBoard.tsx`
- `frontend/src/pages/CompanyDetail.tsx`
- `frontend/src/pages/ContactDetail.tsx`
- `frontend/src/pages/TaskList.tsx`
- `frontend/src/components/pipeline/`
- `frontend/src/components/company/`
- `frontend/src/components/tasks/`
- `frontend/src/api/`
- `frontend/src/hooks/`
- `frontend/src/types/`

## Avoid

- Import manager.
- Ritchie proposal queue.
- Portfolio dashboard.
- Backend code.

## Expected Output

- Pipeline board with configurable status columns.
- Company detail page with profile, completeness, active rubric surface, interactions, tasks, and documents.
- Contact detail page.
- Task list and task form.
- API hooks for core CRM entities.

## Tests To Add Or Run

- Frontend typecheck.
- Component tests for key states if test stack exists.

## Definition Of Done

- Internal users can navigate core CRM workflows.
- UI uses backend server state through TanStack Query.
- Text and controls fit responsive layouts.
