# Agent 22: Frontend Imports, Ritchie, And Portfolio

## Goal

Implement Dealroom import UI, Ritchie proposal review queue, and portfolio dashboard.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `20_FRONTEND_FOUNDATION.md`
- Backend endpoints for imports, agent proposals/audit/context, investments, portfolio metrics, and analytics.

## May Edit

- `frontend/src/pages/ImportManager.tsx`
- `frontend/src/pages/PortfolioDashboard.tsx`
- Proposal queue page/component if added.
- `frontend/src/components/proposals/`
- `frontend/src/api/importsApi.ts`
- `frontend/src/api/agentApi.ts`
- `frontend/src/api/investmentsApi.ts`
- `frontend/src/api/portfolioMetricsApi.ts`
- `frontend/src/api/analyticsApi.ts`
- Related hooks/types/components.

## Avoid

- Backend code.
- Core pipeline/company UI unless needed for navigation.

## Expected Output

- CSV upload and preview screen.
- Conflict/skipped row review.
- Commit action and import batch detail.
- Ritchie proposal queue with approve/reject actions.
- Agent audit/proposal status surfaces.
- Portfolio dashboard with fund and portfolio metrics.

## Tests To Add Or Run

- Frontend typecheck.
- Component tests for import/proposal states if available.

## Definition Of Done

- Users can review Dealroom imports before commit.
- Users can review Ritchie proposals safely.
- Portfolio metrics are visible in a dashboard.
