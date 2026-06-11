# Agent 03: Auth, Users, And Permissions

## Goal

Implement Google OAuth session flow, user creation, role fields, first-admin behavior, scoped Ritchie API key authentication, and centralized permission checks.

## Read First

- `planning/PLAN_v1.md`
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `01_BACKEND_FOUNDATION.md`
- `02_MODELS_MIGRATIONS.md`

## May Edit

- `backend/app/api/routes/auth.py`
- `backend/app/api/routes/users.py`
- `backend/app/core/security.py`
- `backend/app/core/permissions.py`
- `backend/app/core/dependencies.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/permission_service.py`
- `backend/app/repositories/users.py`
- `backend/app/integrations/google_oauth.py`
- `backend/scripts/promote_admin.py`
- `backend/scripts/rotate_agent_key.py`
- `.env.example`
- Auth/user tests.

## Avoid

- Company/deal workflow implementation.
- Ritchie proposal execution beyond authenticating the agent role.
- Frontend OAuth UI.

## Expected Output

- Google OAuth login path and callback service logic.
- Domain allowlist for `@rit.edu` and `@g.rit.edu`.
- User record creation on first successful login.
- First valid login becomes admin or equivalent seed/admin bootstrap path exists.
- Ritchie scoped API key works only for agent surfaces.
- Central `require_permission(user, action, resource)` exists and is permissive in v1 except restricted admin/agent boundaries.

## Tests To Add Or Run

- Auth domain allowlist tests.
- First-admin behavior test.
- Permission guard tests.
- Agent key accept/reject tests.

## Definition Of Done

- Human users and Ritchie have distinct authentication paths.
- Ritchie's key cannot access ordinary user routes.
- Role fields exist from day one even if most v1 permission checks are permissive.
