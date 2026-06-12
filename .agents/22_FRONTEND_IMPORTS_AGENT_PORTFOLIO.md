# Agent 22: Frontend Imports, Ritchie, And Portfolio

## Goal

Implement the Dealroom import UI, the Ritchie activity view (agent audit log + authorization policy toggles), and the portfolio dashboard.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `20_FRONTEND_FOUNDATION.md`
- Backend endpoints for imports, agent policy/audit/context, investments, portfolio metrics, and analytics.

## May Edit

- `frontend/src/pages/ImportManager.tsx`
- `frontend/src/pages/PortfolioDashboard.tsx`
- Ritchie activity page/component if added.
- `frontend/src/components/agent/` (`AgentAuditLog.tsx`, `PolicyPanel.tsx`)
- `frontend/src/api/importsApi.ts`
- `frontend/src/api/agentApi.ts`
- `frontend/src/api/investmentsApi.ts`
- `frontend/src/api/portfolioMetricsApi.ts`
- `frontend/src/api/analyticsApi.ts`
- Related hooks and components. Regenerate `frontend/src/types/` from OpenAPI — do not hand-edit.

## Avoid

- Building any proposal review queue or approve/reject UI — the per-change approval workflow was removed from the plan. Ritchie governance is a binary authorized/blocked policy.
- Backend code.
- Core pipeline/company UI unless needed for navigation.

## Expected Output

- CSV upload and preview screen.
- Conflict/skipped row review.
- Commit action and import batch detail.
- Ritchie activity view: `AgentAuditLog.tsx` feed showing authorized writes and `policy_blocked` attempts, with source/confidence detail.
- `PolicyPanel.tsx`: authorized/blocked toggles per Ritchie tool/field, grouped by tool/action; changes apply immediately via the policy endpoints.
- Portfolio dashboard with fund and portfolio metrics.

## Tests To Add Or Run

- Frontend typecheck.
- Component tests for import states and the policy toggle flow if available.

## Definition Of Done

- Users can review Dealroom imports before commit.
- Users can see what Ritchie did and attempted, and flip tool/field authorization from the UI.
- Portfolio metrics are visible in a dashboard.
