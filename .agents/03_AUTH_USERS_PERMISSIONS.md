# Agent 03: Auth, Users, And Permissions

## Goal

Implement Google OAuth session flow, user creation, role fields for future use, scoped Ritchie API key authentication, and centralized permission checks. In v1, all authenticated human users have the same page access.

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
- `backend/scripts/promote_admin.py` only if a future role helper is still useful.
- `backend/scripts/rotate_agent_key.py`
- `.env.example`
- Auth/user tests.

## Avoid

- Company/deal workflow implementation.
- Ritchie proposal execution beyond authenticating the agent role.
- Frontend OAuth UI.

## Expected Output

- Google OAuth login path and callback service logic.
- Domain allowlist for eligible RIT Google accounts, especially emails ending in `@g.rit.edu`.
- V1 allows anyone with an eligible RIT Google account to log in.
- Future-ready structure for invite-gated login, where a user must have both an eligible RIT Google email and a pre-existing invitation or approved account record.
- User record creation on first successful login.
- Role field exists for future use, but v1 does not need first-admin behavior or separate admin page access.
- Ritchie scoped API key works only for agent surfaces.
- Central `require_permission(user, action, resource)` exists and is permissive for authenticated human users in v1.
- Ritchie remains scoped separately from human users and can only access agent surfaces.

## Tests To Add Or Run

- Auth domain allowlist tests, including `@g.rit.edu`.
- Future invite-gating tests can be skipped or marked pending until that feature is implemented.
- Permission guard tests showing authenticated human users have equal v1 access.
- Agent key accept/reject tests.

## Definition Of Done

- Human users and Ritchie have distinct authentication paths.
- Ritchie's key cannot access ordinary user routes.
- Role fields exist from day one for future use, but v1 human page access is the same for everyone.
