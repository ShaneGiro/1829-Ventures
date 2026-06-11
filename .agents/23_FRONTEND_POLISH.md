# Agent 23: Frontend Polish And Integration

## Goal

Polish the frontend, verify responsiveness, handle loading/error/empty states, and run end-to-end smoke flows against the backend.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`
- All frontend agent briefs.

## Depends On

- `21_FRONTEND_CRM_WORKFLOWS.md`
- `22_FRONTEND_IMPORTS_AGENT_PORTFOLIO.md`

## May Edit

- `frontend/src/`
- `frontend/package.json`
- `nginx/nginx.conf`
- Frontend tests.
- Minor backend API compatibility fixes only if explicitly coordinated.

## Avoid

- Large backend changes.
- New product scope.

## Expected Output

- Responsive layouts for desktop and mobile.
- Loading, error, empty, and permission-denied states.
- Consistent forms and validation.
- Navigation is coherent.
- API errors are shown clearly.
- End-to-end smoke flows work locally.

## Tests To Add Or Run

- Frontend typecheck.
- Frontend lint.
- Build.
- Browser smoke tests if Playwright or equivalent exists.

## Definition Of Done

- Frontend is usable for the v1 internal workflow.
- No major visual overlap or layout breakage.
- App can be served by nginx against the backend.
