# Agent 20: Frontend Foundation

## Goal

Create the React/Vite frontend foundation after backend API contracts are stable.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`
- Backend API docs or OpenAPI output, if available.

## Depends On

- `10_BACKEND_REVIEW_HARDENING.md` or stable mocked API contracts.

## May Edit

- `frontend/`
- `nginx/nginx.conf`
- `docker-compose.yml` only for frontend service wiring.
- Frontend docs if needed.

## Avoid

- Backend feature implementation.
- Changing API contracts without coordinating with backend agents.

## Expected Output

- Vite React TypeScript app boots.
- shadcn/ui and Tailwind setup exists.
- React Router route tree exists.
- App shell and sidebar exist.
- API client and auth hook exist.
- TanStack Query provider is wired.
- Basic protected-route/session handling exists.
- OpenAPI type generation is wired: an npm script runs `openapi-typescript` against the backend OpenAPI spec and writes `frontend/src/types/`. Generated types are the only domain types — no hand-written Pydantic mirrors. Zod is used for form validation only.
- Frontend lint/typecheck/test steps are added to `.github/workflows/ci.yml`.

## Tests To Add Or Run

- Frontend typecheck.
- Basic component/render smoke test if test stack exists.

## Definition Of Done

- Frontend dev server starts.
- App shell renders.
- API client has a stable pattern for the remaining frontend agents.
