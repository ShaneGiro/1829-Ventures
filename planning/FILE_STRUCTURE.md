1829-Ventures/
├── .editorconfig                        # consistent formatting across all editors
├── .gitignore
├── Makefile                             # dev, test, migrate, lint targets
├── README.md
├── PLAN v1.md
├── 1829 Ventures Screening Rubric.pdf
├── Dealroom Data (6.10.26).csv
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml              # stub now, wired in v2 deployment
│
├── backend/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── pyproject.toml                   # project metadata, mypy, ruff, pytest config
│   ├── requirements.txt                 # pip install -r requirements.txt (see CPU torch note at top)
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── scripts/
│   │   ├── seed_funds.py                # creates Beta and Fund I records
│   │   ├── promote_admin.py             # promotes a user to admin before admin UI exists
│   │   └── rotate_agent_key.py          # rotates Ritchie's scoped API key
│   ├── tests/
│   │   ├── conftest.py                  # shared fixtures: db session, test client, auth headers
│   │   ├── unit/
│   │   │   ├── conftest.py
│   │   │   ├── test_pipeline_service.py
│   │   │   ├── test_diligence_service.py
│   │   │   ├── test_dealroom_csv.py
│   │   │   ├── test_agent_tools.py
│   │   │   ├── test_agent_contracts.py  # validates tool JSON Schemas match Pydantic models
│   │   │   ├── test_approval_service.py
│   │   │   └── test_idempotency.py
│   │   ├── integration/
│   │   │   ├── conftest.py
│   │   │   ├── test_dealroom_import.py
│   │   │   ├── test_gmail_ingestion.py
│   │   │   ├── test_agent_proposals.py
│   │   │   ├── test_agent_replay.py     # replays recorded agent payloads without live Claude API
│   │   │   └── test_analytics.py
│   │   └── fixtures/                    # recorded agent job payloads for replay tests
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── py.typed                     # PEP 561 marker — enables mypy/pyright on this package
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── middleware.py            # rate limiting by role + endpoint tier, request ID injection
│       │   ├── router.py                # single include point for all sub-routers
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── auth.py
│       │       ├── users.py
│       │       ├── companies.py
│       │       ├── people.py
│       │       ├── deals.py
│       │       ├── investments.py
│       │       ├── portfolio_metrics.py
│       │       ├── interactions.py
│       │       ├── tasks.py
│       │       ├── documents.py
│       │       ├── email.py             # /email/gmail
│       │       ├── imports.py           # /imports/dealroom
│       │       ├── agent.py             # /agent + /agent/context + /agent/audit
│       │       ├── deal_statuses.py     # admin CRUD for configurable pipeline stages
│       │       └── analytics.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── user.py
│       │   ├── company.py
│       │   ├── person.py
│       │   ├── affiliation.py           # RIT relationship, graduation year, roles
│       │   ├── company_contact.py       # M2M join: company_id, person_id, is_primary, role
│       │   ├── interaction.py
│       │   ├── deal.py
│       │   ├── rubric.py                # 15 sub-scores + computed composite + knockout gates
│       │   ├── diligence_checklist_item.py  # evidence checklist per deal: item, status, completed_by, completed_at
│       │   ├── deal_status.py           # configurable pipeline stage: name, sort_order, color, is_system
│       │   ├── fund.py
│       │   ├── investment.py
│       │   ├── portfolio_metric.py
│       │   ├── document.py
│       │   ├── task.py
│       │   ├── tag.py
│       │   ├── import_batch.py          # job-level metadata: source, status, committed_at
│       │   ├── import_row.py            # per-record: raw data, field provenance, row status (committed/skipped/conflict)
│       │   ├── audit_log.py             # human edits
│       │   ├── ai_audit_log.py          # Ritchie writes — intentionally separate from human audit
│       │   ├── agent_event_log.py
│       │   ├── agent_proposal.py
│       │   └── notification.py
│       │
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── company.py
│       │   ├── person.py
│       │   ├── company_contact.py
│       │   ├── deal.py
│       │   ├── rubric.py
│       │   ├── diligence_checklist_item.py
│       │   ├── deal_status.py
│       │   ├── fund.py
│       │   ├── investment.py
│       │   ├── portfolio_metric.py
│       │   ├── interaction.py
│       │   ├── task.py
│       │   ├── document.py
│       │   ├── import_batch.py
│       │   ├── import_row.py            # preview row, conflict diff, commit/skip status
│       │   ├── agent.py                 # tool definitions + proposal schemas
│       │   └── analytics.py
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py                  # shared query helpers — not a mandatory abstraction for all repos
│       │   ├── users.py
│       │   ├── companies.py
│       │   ├── people.py
│       │   ├── deals.py
│       │   ├── investments.py
│       │   ├── interactions.py
│       │   ├── tasks.py
│       │   ├── documents.py
│       │   ├── imports.py
│       │   ├── agent.py
│       │   ├── deal_statuses.py
│       │   └── analytics.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── permission_service.py    # require_permission() guard — always True in v1
│       │   ├── company_service.py
│       │   ├── deal_service.py
│       │   ├── pipeline_service.py      # status transitions, triage, pass/monitor logic
│       │   ├── diligence_service.py     # rubric scoring, checklist, gate enforcement
│       │   ├── task_service.py
│       │   ├── document_service.py
│       │   ├── dealroom_import_service.py
│       │   ├── gmail_ingestion_service.py
│       │   ├── agent_service.py         # trusted write routing, proposal creation
│       │   ├── approval_service.py      # proposal lifecycle: create → notify → expire → approve/reject
│       │   ├── audit_service.py
│       │   ├── notification_service.py  # NotificationService abstraction (channel-agnostic)
│       │   ├── search_service.py        # keyword (tsvector + GIN) + semantic (pgvector HNSW)
│       │   └── analytics_service.py
│       │
│       ├── agent/                       # CRM-side Ritchie integration surface (not Ritchie itself)
│       │   ├── __init__.py
│       │   ├── tools.py                 # typed tool definitions + permission tier tags
│       │   ├── policy.py                # configurable trusted/approval_required policy (admin-editable at runtime)
│       │   ├── context.py               # RAG context assembly: query → embed → top-K pgvector neighbors
│       │   └── mcp_server.py            # SSE MCP endpoint (/mcp/sse) — must use SSE transport to match kernelbot conf/mcp.json
│       │
│       ├── workers/
│       │   ├── __init__.py
│       │   ├── celery_app.py
│       │   └── jobs/
│       │       ├── __init__.py
│       │       ├── dealroom_import_jobs.py
│       │       ├── gmail_jobs.py        # secondary processing after kernelbot ingest: embed interactions, fire task creation
│       │       ├── agent_jobs.py        # CRM event fanout → kernelbot queue
│       │       ├── embedding_jobs.py    # sentence-transformers → pgvector writes
│       │       ├── notification_jobs.py # daily digest, task assignment emails
│       │       └── analytics_jobs.py
│       │
│       ├── integrations/
│       │   ├── __init__.py
│       │   ├── google_oauth.py
│       │   ├── sendgrid.py
│       │   ├── storage.py               # abstract S3-compatible interface (Protocol)
│       │   ├── minio_storage.py         # MinIO implementation — swap for R2 with one env var
│       │   ├── dealroom_csv.py          # CSV parsing, column mapping, metadata row detection
│       │   ├── ritchie_client.py        # enqueue JSON events to kernelbot queue volume
│       │   └── embeddings.py            # sentence-transformers wrapper (all-MiniLM-L6-v2)
│       │
│       └── core/
│           ├── __init__.py
│           ├── config.py                # env-var settings via pydantic BaseSettings
│           ├── database.py              # SQLAlchemy engine, session factory, get_session
│           ├── dependencies.py          # FastAPI Depends() providers
│           ├── security.py              # JWT signing/verification, API key hashing
│           ├── permissions.py           # role constants, future permission matrix
│           ├── idempotency.py           # idempotency key generation and dedup check
│           ├── audit.py                 # audit context helpers, decorator
│           ├── constants.py             # SECTOR_TAXONOMY, SCORE_THRESHOLDS, seed pipeline status labels
│           ├── exceptions.py            # typed HTTP exception hierarchy
│           ├── logging.py               # structured logging config (Google Cloud Logging compatible)
│           └── types.py                 # shared TypeVar, Protocol, ModelT, SchemaT type aliases
│
├── frontend/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json               # separate tsconfig for vite.config.ts
│   ├── vite.config.ts
│   ├── eslint.config.js
│   ├── prettier.config.js
│   └── src/
│       ├── env.d.ts                     # ImportMetaEnv augmentation for Vite env vars
│       ├── main.tsx
│       ├── App.tsx
│       ├── router.tsx                   # React Router v6 route tree
│       ├── api/
│       │   ├── client.ts                # base fetch/axios client, auth headers, error normalisation
│       │   ├── authApi.ts
│       │   ├── companiesApi.ts
│       │   ├── peopleApi.ts
│       │   ├── dealsApi.ts
│       │   ├── investmentsApi.ts
│       │   ├── portfolioMetricsApi.ts
│       │   ├── interactionsApi.ts
│       │   ├── documentsApi.ts
│       │   ├── tasksApi.ts
│       │   ├── agentApi.ts
│       │   ├── importsApi.ts
│       │   └── analyticsApi.ts
│       ├── types/
│       │   ├── index.ts                 # re-exports all domain types — eventually generated from OpenAPI schema
│       │   ├── common.ts                # PaginatedResponse<T>, ApiError, SortOrder, etc.
│       │   ├── company.ts
│       │   ├── person.ts
│       │   ├── deal.ts
│       │   ├── investment.ts
│       │   ├── portfolioMetric.ts
│       │   ├── interaction.ts
│       │   ├── document.ts
│       │   ├── task.ts
│       │   ├── agent.ts                 # proposal, tool definition, audit entry types
│       │   └── analytics.ts
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   ├── useCompanies.ts
│       │   ├── useDeals.ts
│       │   ├── useTasks.ts
│       │   └── useAgent.ts
│       ├── lib/
│       │   ├── utils.ts                 # cn(), date formatting, currency formatting
│       │   ├── validators.ts            # Zod schemas that mirror backend Pydantic schemas
│       │   └── constants.ts             # sector labels, status display strings, UI-facing copy
│       ├── components/
│       │   ├── ui/                      # shadcn/ui primitives (Button, Card, Dialog, Badge, etc.)
│       │   ├── layout/
│       │   │   ├── AppShell.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── index.ts             # barrel export
│       │   ├── pipeline/
│       │   │   ├── KanbanBoard.tsx
│       │   │   ├── KanbanColumn.tsx
│       │   │   ├── DealCard.tsx
│       │   │   └── index.ts
│       │   ├── company/
│       │   │   ├── CompanyCard.tsx
│       │   │   ├── CompanyProfile.tsx
│       │   │   ├── RubricPanel.tsx
│       │   │   ├── InteractionList.tsx
│       │   │   └── index.ts
│       │   ├── tasks/
│       │   │   ├── TaskCard.tsx
│       │   │   ├── TaskForm.tsx
│       │   │   └── index.ts
│       │   └── proposals/
│       │       ├── ProposalCard.tsx
│       │       ├── ProposalQueue.tsx
│       │       └── index.ts
│       └── pages/
│           ├── PipelineBoard.tsx
│           ├── CompanyDetail.tsx
│           ├── ContactDetail.tsx
│           ├── PortfolioDashboard.tsx
│           ├── TaskList.tsx
│           ├── ImportManager.tsx
│           └── Auth.tsx
│
├── nginx/
│   └── nginx.conf
│
└── docker/
    ├── postgres/
    ├── redis/
    └── minio/
