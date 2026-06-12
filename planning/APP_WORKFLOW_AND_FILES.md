# 1829 Ventures CRM: App Workflow And File Guide

This document explains how the app is expected to work and what each file in `planning/FILE_STRUCTURE.md` is responsible for.

## How The App Works

1829 Ventures CRM is an internal operating system for managing alumni founder relationships, deal flow, portfolio tracking, tasks, documents, Dealroom imports, Gmail ingestion, analytics, and Ritchie, the AI agent.

The core runtime flow is:

```text
React frontend -> nginx -> FastAPI API -> service layer -> repositories -> Postgres/PostGIS/pgvector
                                      |
                                      v
                              Redis job queue -> Celery workers
                                      |
                                      v
                         imports, email ingestion, embeddings,
                         notifications, analytics, Ritchie fanout
```

## Main User Workflows

### Authentication

Users log in through Google OAuth. In v1, the backend accepts eligible RIT Google accounts, especially emails ending in `@g.rit.edu`, creates accounts on first eligible login, and issues a session/JWT through an HTTP-only cookie. This means anyone with an approved RIT Google email domain can log in during v1. All authenticated human users have the same page access in v1; there is no separate admin page experience. A future version will add invitation gating so a user must have both an eligible RIT Google email and a pre-existing invitation or approved account record. Ritchie does not use Google OAuth; it uses a scoped API key and is restricted to `/agent/*` and MCP-facing functionality.

### Company-Centered CRM

The primary workspace is the company record. A company can be created with only a name. Missing information is tracked through completeness fields instead of blocking creation. The company record connects to people, contacts, affiliations, interactions, deals, documents, tags, tasks, import provenance, and agent activity.

During the frontend phase near the end of v1, the company detail page should become the main company workspace. It should display all important company information in a logical layout and include an in-page, fillable screening rubric tied to the active investment opportunity, so users can evaluate the company without leaving the page.

### People And Contacts

People represent founders, alumni, LP contacts, advisors, faculty experts, co-investors, and operators. `CompanyContact` links people to companies, including the primary contact used by default workflows. `Affiliation` captures RIT relationship information such as graduation year, program, and roles.

### Deal Pipeline

Deals represent investment opportunities. A company may have multiple deals over time, including follow-ons. The app separates relationship status from investment status so outbound alumni outreach does not automatically count as active investment pipeline. Review-needed triage can start investment review, mark a company for monitoring, or pass with reason tags.

### Diligence And Rubric

Every active investment opportunity gets diligence workflow tracking and a screening rubric. The rubric stores knockout gates, 15 sub-scores, weighted category scores, and a computed composite score. Rubric writes are blocked for Ritchie by default; the team can authorize the rubric tool in the runtime policy if they want Ritchie writing drafted scores directly.

### Funds, Investments, And Portfolio Metrics

Funds are first-class records. Investments link a fund, company, and optionally a deal. Portfolio metrics track revenue, runway, headcount, valuation marks, TVPI/DPI/IRR inputs, and reporting periods. Analytics are calculated per fund and across the portfolio.

### Dealroom Import

Dealroom CSV uploads are parsed in a preview-first workflow. The importer detects metadata rows, maps columns, splits semicolon-delimited multi-value fields, detects duplicates and conflicts, and stores raw row provenance. Clean rows can be committed while unresolved rows remain attached to the import batch for later review.

### Gmail Ingestion

Team members forward emails to Ritchie's Gmail address. Kernelbot watches that inbox and notifies the CRM. The CRM stores matched emails as interactions, captures provenance, queues unmatched emails for review, and stores small attachments in S3-compatible object storage.

### Documents

Documents store metadata in Postgres and file bodies in S3-compatible storage. Local v1 uses MinIO; later deployments can swap to Cloudflare R2 or another compatible service by changing environment configuration.

### Tasks And Notifications

Tasks support follow-ups, monitor reminders, diligence work, assignments, and Ritchie-suggested next steps. Notifications are surfaced in-app/API and via SendGrid email. Daily task digests run at 9:00 AM America/New_York.

### Search And Analytics

Keyword search uses Postgres full-text search. Semantic search uses pgvector with locally generated sentence-transformer embeddings. Analytics cover pipeline, portfolio, source, sector, interaction cadence, thesis fit, and agent activity.

### Ritchie Agent Integration

Ritchie is treated as a first-class actor. The backend exposes typed tools, a binary authorization policy, RAG context, and MCP (Streamable HTTP) integration. Every tool/field is either authorized — executed directly, audited, and idempotent — or blocked, in which case the call is rejected and logged until a human updates the policy setting. There is no per-change approval or proposal workflow.

## File And Directory Reference

### Repository Root

| Path | Purpose |
| --- | --- |
| `.editorconfig` | Keeps indentation, line endings, and formatting consistent across editors. |
| `.gitignore` | Excludes generated files, secrets, local environments, and build artifacts from Git. |
| `.github/workflows/ci.yml` | GitHub Actions CI: ruff, mypy, backend tests with coverage, and frontend lint/typecheck/tests on every push and PR. |
| `Makefile` | Provides shortcuts for common tasks such as dev, test, migrate, lint, and format. |
| `README.md` | High-level project overview, architecture summary, and getting-started guide. |
| `planning/PLAN_v1.md` | Product and technical plan for the v1 CRM. |
| `planning/1829 Ventures Screening Rubric.pdf` | Canonical screening rubric reference for diligence and Ritchie rubric drafting. |
| `Dealroom Data (6.10.26).csv` | Seed/source dataset exported from Dealroom. |
| `.env.example` | Example environment variables for local setup. |
| `docker-compose.yml` | Local development stack: API, frontend, Postgres/PostGIS/pgvector, Redis, MinIO, worker, and nginx as needed. |
| `docker-compose.prod.yml` | Production deployment stub for later RIT/server deployment. |

### `backend/`

| Path | Purpose |
| --- | --- |
| `backend/.dockerignore` | Keeps local caches and unnecessary files out of backend Docker builds. |
| `backend/Dockerfile` | Builds the FastAPI and worker runtime image. |
| `backend/pyproject.toml` | Backend project metadata and tool configuration for mypy, ruff, pytest, and related tools. |
| `backend/requirements.txt` | Pip dependency list, including CPU-friendly install notes where needed. |
| `backend/alembic.ini` | Alembic migration configuration. |

### `backend/alembic/`

| Path | Purpose |
| --- | --- |
| `backend/alembic/env.py` | Alembic runtime configuration that loads app models and database settings. |
| `backend/alembic/versions/` | Generated migration files. |

### `backend/scripts/`

| Path | Purpose |
| --- | --- |
| `backend/scripts/seed_funds.py` | Creates initial fund records for Beta and Fund I. |
| `backend/scripts/promote_admin.py` | Optional future helper for role testing; v1 does not distinguish admin and normal user page access. |
| `backend/scripts/rotate_agent_key.py` | Rotates Ritchie's scoped API key. |
| `backend/scripts/backup_db.sh` | Nightly `pg_dump` backup: compresses dumps, retains 14 days, copies each dump off the VM. |

### `backend/tests/`

Coverage note: code coverage should be tracked as part of the test workflow. Backend Python coverage should use `coverage.py` through `pytest-cov`. Frontend TypeScript coverage should use Vitest coverage with the V8/Istanbul provider. JaCoCo is not planned unless a Java/JVM component is added later.

| Path | Purpose |
| --- | --- |
| `backend/tests/conftest.py` | Shared pytest fixtures for DB sessions, test client, and auth headers. |
| `backend/tests/unit/conftest.py` | Unit-test-only fixtures. |
| `backend/tests/unit/test_pipeline_service.py` | Tests pipeline transitions, triage, monitor, pass, and start-review behavior. |
| `backend/tests/unit/test_diligence_service.py` | Tests rubric scoring, gates, checklist rules, and computed totals. |
| `backend/tests/unit/test_dealroom_csv.py` | Tests CSV metadata row detection, parsing, splitting, and mapping. |
| `backend/tests/unit/test_agent_tools.py` | Tests Ritchie tool definitions, permission tiers, and tool construction. |
| `backend/tests/unit/test_agent_contracts.py` | Confirms tool JSON Schemas match the Pydantic models they map to. |
| `backend/tests/unit/test_agent_policy.py` | Tests binary authorized/blocked policy enforcement and runtime policy updates. |
| `backend/tests/unit/test_idempotency.py` | Tests stable idempotency keys and duplicate-write prevention. |
| `backend/tests/integration/conftest.py` | Integration-test fixtures for DB-backed flows. |
| `backend/tests/integration/test_dealroom_import.py` | Tests upload, preview, conflict review, and commit behavior. |
| `backend/tests/integration/test_gmail_ingestion.py` | Tests forwarded email ingestion into CRM interactions. |
| `backend/tests/integration/test_agent_policy_flow.py` | Tests blocked tool calls being rejected and logged, runtime authorization changes, and audit behavior. |
| `backend/tests/integration/test_agent_replay.py` | Replays recorded agent payloads without live AI calls. |
| `backend/tests/integration/test_analytics.py` | Tests dashboard and analytics query behavior. |
| `backend/tests/fixtures/` | Stores recorded agent job payloads and other test fixtures. |

### `backend/app/`

| Path | Purpose |
| --- | --- |
| `backend/app/__init__.py` | Marks the backend app as a Python package. |
| `backend/app/main.py` | Creates and configures the FastAPI app. |
| `backend/app/py.typed` | Marks the package as typed for mypy and pyright. |

### `backend/app/api/`

| Path | Purpose |
| --- | --- |
| `backend/app/api/__init__.py` | Marks the API package. |
| `backend/app/api/middleware.py` | Adds request ID injection and Redis token-bucket rate limiting by role and endpoint tier. |
| `backend/app/api/router.py` | Single include point for all API route modules. |
| `backend/app/api/routes/__init__.py` | Marks the routes package. |
| `backend/app/api/routes/auth.py` | Google OAuth login, callback, session refresh, logout, and current user endpoints. |
| `backend/app/api/routes/users.py` | Internal user records and role metadata for future permissions; v1 human users have the same page access. |
| `backend/app/api/routes/companies.py` | Company CRUD, completeness, source provenance, tags, and profile fields. |
| `backend/app/api/routes/people.py` | People CRUD and RIT affiliation-related endpoints. |
| `backend/app/api/routes/deals.py` | Deal/opportunity CRUD, diligence, pipeline movements, and decisions. |
| `backend/app/api/routes/investments.py` | Investment records, ownership inputs, instruments, and fund linkage. |
| `backend/app/api/routes/portfolio_metrics.py` | Portfolio reporting snapshots and performance inputs. |
| `backend/app/api/routes/interactions.py` | Notes, calls, meetings, emails, intros, and diligence conversations. |
| `backend/app/api/routes/tasks.py` | Task creation, assignment, completion, reassignment, and queues. |
| `backend/app/api/routes/documents.py` | Document metadata, presigned uploads, and links to companies/deals/people. |
| `backend/app/api/routes/email.py` | Gmail-related email ingestion and review endpoints. |
| `backend/app/api/routes/imports.py` | Dealroom upload, preview, conflict review, commit, and skipped-row inspection. |
| `backend/app/api/routes/agent.py` | Ritchie `/agent`, `/agent/context`, `/agent/audit`, and authorization policy endpoints. |
| `backend/app/api/routes/deal_statuses.py` | CRUD for configurable pipeline stages; no v1 admin-only page distinction. |
| `backend/app/api/routes/analytics.py` | Pipeline, portfolio, source, sector, interaction, thesis, and agent analytics endpoints. |

### `backend/app/models/`

| Path | Purpose |
| --- | --- |
| `backend/app/models/__init__.py` | Imports/registers SQLAlchemy models for migrations and metadata. |
| `backend/app/models/base.py` | Declarative base, timestamps, IDs, soft-delete `archived_at`, and shared model helpers. |
| `backend/app/models/user.py` | Authenticated human users and Ritchie's agent identity/role. |
| `backend/app/models/company.py` | Company profile, CRM source-of-truth fields, statuses, completeness, and Dealroom IDs. |
| `backend/app/models/person.py` | Founder, alumni, LP, advisor, faculty, co-investor, and operator records. |
| `backend/app/models/affiliation.py` | RIT relationship metadata and roles connecting people to 1829's thesis. |
| `backend/app/models/company_contact.py` | Company-person join table with primary contact and role fields. |
| `backend/app/models/interaction.py` | Emails, calls, meetings, notes, intros, and relationship touchpoints. |
| `backend/app/models/deal.py` | Investment opportunities, relationship status, investment status, round info, and decision notes. |
| `backend/app/models/rubric.py` | Knockout gates, 15 rubric sub-scores, weighted categories, and composite score. |
| `backend/app/models/diligence_checklist_item.py` | Per-deal diligence evidence items and completion history. |
| `backend/app/models/deal_status.py` | Configurable pipeline stage records with order, color, and system flags. |
| `backend/app/models/fund.py` | Fund records such as Beta and Fund I. |
| `backend/app/models/investment.py` | Fund-company investments, amount, date, instrument, valuation inputs, and ownership snapshots. |
| `backend/app/models/portfolio_metric.py` | Revenue, runway, headcount, marks, TVPI/DPI/IRR inputs, and reporting period. |
| `backend/app/models/document.py` | Document metadata, storage keys, external links, source system, and related entities. |
| `backend/app/models/task.py` | Follow-ups, reminders, diligence tasks, assignments, status, priority, and history. |
| `backend/app/models/tag.py` | User-created tags, protected system tags, archived tags, and pass reason tags. |
| `backend/app/models/import_batch.py` | Import-level metadata such as source, upload user, status, summary counts, and commit time. |
| `backend/app/models/import_row.py` | Raw row payloads, per-field provenance, row status, conflicts, skipped reasons, and matches. |
| `backend/app/models/audit_log.py` | Audit entries for every CRM create, update, and archive, with actor, timestamp, and old/new values. |
| `backend/app/models/ai_audit_log.py` | Ritchie intent, trusted writes, old/new values, source, confidence, idempotency, and result. |
| `backend/app/models/agent_event_log.py` | Events emitted to Ritchie, processing status, payload hash, response summary, and `policy_blocked` rejections. |
| `backend/app/models/agent_policy.py` | Runtime authorization policy records: tool/field, authorized or blocked, updated by, updated at. |
| `backend/app/models/notification.py` | In-app/API notifications and read-state support. |

### `backend/app/schemas/`

| Path | Purpose |
| --- | --- |
| `backend/app/schemas/__init__.py` | Marks the schema package and may re-export common schemas. |
| `backend/app/schemas/user.py` | Pydantic request/response models for users and auth-facing user data. |
| `backend/app/schemas/company.py` | Company create/update/read/completeness schemas. |
| `backend/app/schemas/person.py` | People and affiliation-facing schemas. |
| `backend/app/schemas/company_contact.py` | Schemas for company contact linking and primary contact selection. |
| `backend/app/schemas/deal.py` | Deal/opportunity schemas and status transition payloads. |
| `backend/app/schemas/rubric.py` | Rubric scoring, knockout gate, and draft/approved score schemas. |
| `backend/app/schemas/diligence_checklist_item.py` | Checklist item read/update/completion schemas. |
| `backend/app/schemas/deal_status.py` | Configurable pipeline stage create/update/read schemas. |
| `backend/app/schemas/fund.py` | Fund schemas. |
| `backend/app/schemas/investment.py` | Investment create/update/read schemas. |
| `backend/app/schemas/portfolio_metric.py` | Portfolio reporting and metric schemas. |
| `backend/app/schemas/interaction.py` | Interaction schemas for notes, meetings, emails, and provenance. |
| `backend/app/schemas/task.py` | Task creation, update, assignment, completion, and queue schemas. |
| `backend/app/schemas/document.py` | Document metadata and presigned upload schemas. |
| `backend/app/schemas/import_batch.py` | Import upload, preview, commit, and batch detail schemas. |
| `backend/app/schemas/import_row.py` | Import preview row, conflict diff, commit/skip status, and provenance schemas. |
| `backend/app/schemas/agent.py` | Ritchie tool definitions, context requests, authorization policy schemas, and audit read models. |
| `backend/app/schemas/analytics.py` | Dashboard and analytics response schemas. |

### `backend/app/repositories/`

| Path | Purpose |
| --- | --- |
| `backend/app/repositories/__init__.py` | Marks the repository package. |
| `backend/app/repositories/base.py` | Small shared query helpers, not a mandatory CRUD framework. |
| `backend/app/repositories/users.py` | User and role-related database queries. |
| `backend/app/repositories/companies.py` | Company search, completeness, provenance, and relation queries. |
| `backend/app/repositories/people.py` | People, contacts, and affiliation queries. |
| `backend/app/repositories/deals.py` | Deal pipeline, diligence, status, and rubric queries. |
| `backend/app/repositories/investments.py` | Fund investment and portfolio-related queries. |
| `backend/app/repositories/interactions.py` | Interaction list, matching, and timeline queries. |
| `backend/app/repositories/tasks.py` | Task queue, assignment, due-date, and digest queries. |
| `backend/app/repositories/documents.py` | Document metadata and entity-link queries. |
| `backend/app/repositories/imports.py` | Import batch, row, conflict, and commit queries. |
| `backend/app/repositories/agent.py` | Agent event, proposal, policy, and audit database queries. |
| `backend/app/repositories/deal_statuses.py` | Configurable pipeline status queries and ordering. |
| `backend/app/repositories/analytics.py` | Aggregation queries for dashboards. |

### `backend/app/services/`

| Path | Purpose |
| --- | --- |
| `backend/app/services/__init__.py` | Marks the service package. |
| `backend/app/services/auth_service.py` | OAuth callback handling, account creation, session/JWT behavior, and agent key auth. |
| `backend/app/services/permission_service.py` | Central `require_permission` guard, permissive for authenticated human users in v1; Ritchie's agent API remains scoped separately. |
| `backend/app/services/company_service.py` | Company business rules, completeness, non-overwrite rules, tags, and provenance. |
| `backend/app/services/deal_service.py` | Deal CRUD, opportunity creation, and deal-level business rules. |
| `backend/app/services/pipeline_service.py` | Relationship/investment status transitions, review-needed triage, monitor, pass, and start-review workflows. |
| `backend/app/services/diligence_service.py` | Diligence checklist, rubric scoring, gates, and score thresholds. |
| `backend/app/services/task_service.py` | Task creation, assignment, reassignment, completion, default owners, and queues. |
| `backend/app/services/document_service.py` | Document metadata, storage coordination, and presigned upload flow. |
| `backend/app/services/dealroom_import_service.py` | Dealroom preview, dedupe, conflict resolution, partial commit, and provenance rules. |
| `backend/app/services/gmail_ingestion_service.py` | Forwarded email normalization, matching, interaction creation, and unmatched review handling. |
| `backend/app/services/agent_service.py` | Authorized-write routing, policy-gate enforcement, and Ritchie-facing service behavior. |
| `backend/app/services/agent_policy_service.py` | Runtime authorization policy reads and updates — audited, immediate effect, no restart required. |
| `backend/app/services/audit_service.py` | Human/system/AI audit recording and audit view support. |
| `backend/app/services/notification_service.py` | Channel-agnostic notification creation and dispatch orchestration. |
| `backend/app/services/search_service.py` | Keyword search, semantic search, embedding lookup, and context retrieval. |
| `backend/app/services/analytics_service.py` | Pipeline, portfolio, source, sector, interaction, thesis, and agent analytics. |

### `backend/app/agent/`

| Path | Purpose |
| --- | --- |
| `backend/app/agent/__init__.py` | Marks the CRM-side agent package. |
| `backend/app/agent/tools.py` | Typed Ritchie tool definitions with JSON Schema and permission tier tags. |
| `backend/app/agent/policy.py` | Runtime-configurable binary authorized/blocked policy. |
| `backend/app/agent/context.py` | RAG context assembly using embeddings and pgvector top-K retrieval. |
| `backend/app/agent/mcp_server.py` | Streamable HTTP MCP endpoint consumed by kernelbot (SSE is deprecated in the MCP spec). |

### `backend/app/workers/`

| Path | Purpose |
| --- | --- |
| `backend/app/workers/__init__.py` | Marks the workers package. |
| `backend/app/workers/celery_app.py` | Celery app setup, broker config, task registration, and retry defaults. |
| `backend/app/workers/jobs/__init__.py` | Marks the worker jobs package. |
| `backend/app/workers/jobs/dealroom_import_jobs.py` | Background CSV parse, preview, dedupe, and commit work. |
| `backend/app/workers/jobs/gmail_jobs.py` | Secondary processing after kernelbot Gmail ingest, including embeddings and task triggers. |
| `backend/app/workers/jobs/agent_jobs.py` | CRM event fanout to Ritchie/kernelbot and agent result processing. |
| `backend/app/workers/jobs/embedding_jobs.py` | Local sentence-transformer embedding generation and pgvector writes. |
| `backend/app/workers/jobs/notification_jobs.py` | Daily digests, task assignment notices, and due-date reminders. |
| `backend/app/workers/jobs/analytics_jobs.py` | Background analytics refreshes or heavy dashboard aggregation work. |

### `backend/app/integrations/`

| Path | Purpose |
| --- | --- |
| `backend/app/integrations/__init__.py` | Marks the integrations package. |
| `backend/app/integrations/google_oauth.py` | Google OAuth client wrapper and profile retrieval. |
| `backend/app/integrations/sendgrid.py` | SendGrid SMTP/API wrapper for transactional email. |
| `backend/app/integrations/storage.py` | Protocol/interface for S3-compatible object storage. |
| `backend/app/integrations/minio_storage.py` | MinIO implementation of the storage interface. |
| `backend/app/integrations/dealroom_csv.py` | Dealroom CSV parser, metadata row detection, column mapping, and value splitting. |
| `backend/app/integrations/ritchie_client.py` | Boundary for sending structured events to kernelbot/Ritchie. |
| `backend/app/integrations/embeddings.py` | Sentence-transformer wrapper for local embeddings. |

### `backend/app/core/`

| Path | Purpose |
| --- | --- |
| `backend/app/core/__init__.py` | Marks the core package. |
| `backend/app/core/config.py` | Environment settings using Pydantic BaseSettings. |
| `backend/app/core/database.py` | Dual SQLAlchemy engines: async (asyncpg) for API request handlers, sync (psycopg2) for Celery workers and Alembic, with matching session factories and `get_session`. |
| `backend/app/core/dependencies.py` | FastAPI dependency providers for DB sessions, current user, permissions, and services. |
| `backend/app/core/security.py` | JWT signing/verification (PyJWT), passwordless auth helpers, and API key hashing. |
| `backend/app/core/permissions.py` | Role constants and future permission matrix. |
| `backend/app/core/idempotency.py` | Idempotency key generation and duplicate-write checks. |
| `backend/app/core/audit.py` | Audit context helpers and decorators. |
| `backend/app/core/constants.py` | Sector taxonomy, score thresholds, and seed/default pipeline status labels. |
| `backend/app/core/exceptions.py` | Typed application and HTTP exception hierarchy. |
| `backend/app/core/logging.py` | Structured logging configuration. |
| `backend/app/core/types.py` | Shared TypeVars, Protocols, and type aliases. |

### `frontend/`

| Path | Purpose |
| --- | --- |
| `frontend/.dockerignore` | Keeps local frontend caches out of Docker builds. |
| `frontend/Dockerfile` | Builds the frontend app for local/prod containers. |
| `frontend/package.json` | Frontend dependencies and npm scripts. |
| `frontend/tsconfig.json` | TypeScript config for the app. |
| `frontend/tsconfig.node.json` | TypeScript config for Node-side files such as `vite.config.ts`. |
| `frontend/vite.config.ts` | Vite configuration. |
| `frontend/eslint.config.js` | Frontend lint configuration. |
| `frontend/prettier.config.js` | Frontend formatting configuration. |

### `frontend/src/`

| Path | Purpose |
| --- | --- |
| `frontend/src/env.d.ts` | Vite environment variable type declarations. |
| `frontend/src/main.tsx` | React app entrypoint. |
| `frontend/src/App.tsx` | Root React component. |
| `frontend/src/router.tsx` | React Router route tree. |

### `frontend/src/api/`

| Path | Purpose |
| --- | --- |
| `frontend/src/api/client.ts` | Shared API client, auth handling, and error normalization. |
| `frontend/src/api/authApi.ts` | Auth/session API calls. |
| `frontend/src/api/companiesApi.ts` | Company API calls. |
| `frontend/src/api/peopleApi.ts` | People and contact API calls. |
| `frontend/src/api/dealsApi.ts` | Deal and pipeline API calls. |
| `frontend/src/api/investmentsApi.ts` | Investment API calls. |
| `frontend/src/api/portfolioMetricsApi.ts` | Portfolio metric API calls. |
| `frontend/src/api/interactionsApi.ts` | Interaction API calls. |
| `frontend/src/api/documentsApi.ts` | Document metadata and upload API calls. |
| `frontend/src/api/tasksApi.ts` | Task API calls. |
| `frontend/src/api/agentApi.ts` | Ritchie policy, context, and audit API calls. |
| `frontend/src/api/importsApi.ts` | Dealroom import API calls. |
| `frontend/src/api/analyticsApi.ts` | Dashboard/analytics API calls. |

### `frontend/src/types/`

| Path | Purpose |
| --- | --- |
| `frontend/src/types/index.ts` | Re-exports domain types, generated from the FastAPI OpenAPI spec via `openapi-typescript` from day one. |
| `frontend/src/types/common.ts` | Shared response/error/sort/pagination types. |
| `frontend/src/types/company.ts` | Company frontend types. |
| `frontend/src/types/person.ts` | Person/contact frontend types. |
| `frontend/src/types/deal.ts` | Deal/pipeline frontend types. |
| `frontend/src/types/investment.ts` | Investment frontend types. |
| `frontend/src/types/portfolioMetric.ts` | Portfolio metric frontend types. |
| `frontend/src/types/interaction.ts` | Interaction frontend types. |
| `frontend/src/types/document.ts` | Document frontend types. |
| `frontend/src/types/task.ts` | Task frontend types. |
| `frontend/src/types/agent.ts` | Agent policy, tool definition, audit entry, and context types. |
| `frontend/src/types/analytics.ts` | Analytics/dashboard frontend types. |

### `frontend/src/hooks/`

| Path | Purpose |
| --- | --- |
| `frontend/src/hooks/useAuth.ts` | Auth/session React Query hook. |
| `frontend/src/hooks/useCompanies.ts` | Company query/mutation hooks. |
| `frontend/src/hooks/useDeals.ts` | Deal and pipeline query/mutation hooks. |
| `frontend/src/hooks/useTasks.ts` | Task query/mutation hooks. |
| `frontend/src/hooks/useAgent.ts` | Ritchie policy/context/audit hooks. |

### `frontend/src/lib/`

| Path | Purpose |
| --- | --- |
| `frontend/src/lib/utils.ts` | Shared UI utilities such as `cn`, date formatting, and currency formatting. |
| `frontend/src/lib/validators.ts` | Zod schemas for client-side form validation only; domain types come from OpenAPI codegen. |
| `frontend/src/lib/constants.ts` | UI-facing labels, sectors, status display values, and copy constants. |

### `frontend/src/components/`

| Path | Purpose |
| --- | --- |
| `frontend/src/components/ui/` | shadcn/ui primitives such as Button, Dialog, Badge, Input, Table, and related UI base components. |
| `frontend/src/components/layout/AppShell.tsx` | Main authenticated application shell. |
| `frontend/src/components/layout/Sidebar.tsx` | Primary navigation sidebar. |
| `frontend/src/components/layout/index.ts` | Barrel export for layout components. |
| `frontend/src/components/pipeline/KanbanBoard.tsx` | Pipeline board container. |
| `frontend/src/components/pipeline/KanbanColumn.tsx` | Pipeline status column. |
| `frontend/src/components/pipeline/DealCard.tsx` | Deal card used on the board. |
| `frontend/src/components/pipeline/index.ts` | Barrel export for pipeline components. |
| `frontend/src/components/company/CompanyCard.tsx` | Compact company card for lists/search. |
| `frontend/src/components/company/CompanyProfile.tsx` | Company profile panel. |
| `frontend/src/components/company/RubricPanel.tsx` | Screening rubric UI. |
| `frontend/src/components/company/InteractionList.tsx` | Company interaction timeline/list. |
| `frontend/src/components/company/index.ts` | Barrel export for company components. |
| `frontend/src/components/tasks/TaskCard.tsx` | Task card/list item. |
| `frontend/src/components/tasks/TaskForm.tsx` | Task creation/edit form. |
| `frontend/src/components/tasks/index.ts` | Barrel export for task components. |
| `frontend/src/components/agent/AgentAuditLog.tsx` | Ritchie activity feed: authorized writes and blocked attempts. |
| `frontend/src/components/agent/PolicyPanel.tsx` | Authorized/blocked toggles per Ritchie tool/field. |
| `frontend/src/components/agent/index.ts` | Barrel export for agent components. |

### `frontend/src/pages/`

| Path | Purpose |
| --- | --- |
| `frontend/src/pages/PipelineBoard.tsx` | Main deal pipeline board page. |
| `frontend/src/pages/CompanyDetail.tsx` | Main company workspace with logically organized company profile information, fillable active rubric, interactions, tasks, and documents. |
| `frontend/src/pages/ContactDetail.tsx` | Person/contact detail page. |
| `frontend/src/pages/PortfolioDashboard.tsx` | Fund and portfolio metrics dashboard. |
| `frontend/src/pages/TaskList.tsx` | User and shared task queues. |
| `frontend/src/pages/ImportManager.tsx` | Dealroom CSV upload, preview, conflict review, and commit UI. |
| `frontend/src/pages/Auth.tsx` | Login/callback/session handling UI. |

### Deployment Directories

| Path | Purpose |
| --- | --- |
| `nginx/nginx.conf` | Serves the frontend and proxies `/api/*` to FastAPI. |
| `docker/postgres/` | Postgres init: `init.sql` enables the PostGIS and pgvector extensions on first start, before the first migration. |
| `docker/redis/` | Redis local configuration, if needed. |
| `docker/minio/` | MinIO init: creates the default buckets on first startup. |

## Boundaries To Preserve

- Routes should handle HTTP only.
- Services should enforce business logic, permissions, non-overwrite rules, workflow transitions, the agent authorization policy, and auditing.
- Repositories should isolate SQLAlchemy queries.
- Integrations should wrap external systems.
- Workers should run slow or asynchronous work outside request/response.
- Ritchie should only interact through the typed API/MCP surface.
- Human-curated CRM fields should remain the source of truth.
