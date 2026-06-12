# 1829 Ventures CRM Backend Plan

## Summary
Build a backend-first CRM for 1829 Ventures: an internal operating system for alumni founder relationships, deal flow, portfolio tracking, AI-assisted data capture, Gmail ingestion, and Dealroom-powered ecosystem mapping.

Use `FastAPI + Postgres/PostGIS`, with Docker Compose for local development and a cloud-ready architecture. The CRM is inspired by Carta's fund/portfolio workflows, but 1829's manually curated CRM remains the source of truth.

The v1 product serves the internal fund team only: managing directors, principals, analysts, and admins. LP/founder portals, fund accounting, capital calls, tax documents, and full Carta integration are deferred.

A persistent AI agent — **Ritchie** — is a first-class backend consumer from day one. Ritchie monitors the entire backend: deal flow, email, portfolio metrics, and analytics. The integration methodology described below is designed to make that relationship seamless, auditable, and safe.

## Key Product Decisions
- Primary workspace: company records.
- Users: internal 1829 team only for v1.
- Access model: all authenticated human users have the same page access in v1. No admin-only page experience is planned for v1.
- Diligence checklist completion is open to any internal user in v1 because the team is currently small; the model should preserve actor/timestamp history so stricter permissions can be added later.
- Source of truth: manually curated 1829 CRM fields win over imported or AI-derived fields.
- Ritchie cannot write a human-curated field unless the authorization policy explicitly allows it.
- Ritchie's authorization policy is strictly binary: every tool/field is either `authorized` (Ritchie executes it directly, fully audited) or `blocked` (Ritchie can never do it until a human updates the policy setting). There is no approval queue, proposal workflow, or per-change human review.
- The authorization policy must be runtime-configurable so fields/actions can move between `authorized` and `blocked` without code rewrites; changes take effect immediately without restart or redeploy and are themselves audited. In v1, if policy editing is exposed at all, all authenticated human users have the same access model; stricter admin-only control is deferred.
- The policy is field-level for record writes, with fields grouped by tool/action so an entire tool/action can be toggled at once when needed.
- Auditability is a core product requirement: every change to the database — manual, import, system, or AI — is recorded with actor, timestamp, old value, and new value.
- Manual company/deal management is the first core workflow; Dealroom import, Gmail sync, and Ritchie automation enrich that foundation.
- Companies actively managed by 1829 are assumed to have an RIT founder or RIT core employee, so users should not be forced to re-enter redundant RIT nexus fields on every company.
- Pipeline model: dual status tracking:
  - Relationship status: identified, contacted, review_needed, active, nurture, strategic, inactive.
  - Investment status: sourced, initial review, diligence, IC review, term sheet, invested, passed, monitor.
  - The two status lanes make the border explicit between alumni/outreach relationship management and actual investment evaluation.
  - Outbound alumni outreach is explicitly separate from the investment pipeline. A company is not considered in the investment pipeline until the founder/company responds or otherwise engages.
  - A founder/company response creates a review-needed state before the team decides whether it becomes an investment opportunity, nurture relationship, monitor record, or alumni-relations-only interaction.
  - Current v1 trigger: founder/company response moves the company to the investment border by creating `review_needed`.
  - Design note: keep the transition configurable enough that this trigger can later change to a manual team decision.
  - Review-needed triage outcomes are: start investment review, monitor, or pass.
  - Completing a review-needed triage task requires choosing one of the triage outcomes.
  - Choosing start investment review automatically creates the first investment opportunity, sets investment status to `initial review`, initializes the diligence checklist, and attaches the screening rubric.
  - Pass means no current investment fit, not a cutoff from alumni relationship management.
  - Pass decisions require one or more reason tags, so the team can later analyze and reactivate companies by pass reason.
  - Monitor decisions require a next-check date and can include optional reason tags.
  - When a monitored company reaches its next-check date, the system creates a task/reminder and moves it back to review_needed for reassessment.
- Analytics priority: pipeline dashboards first. Geography map view is deferred to a later release.
- Investment-fit scoring is supported by a separate confidence/completeness trust indicator; automated ranking order is deferred.
- Carta influence: fund CRM, portfolio tracking, company/investment records, valuation/performance inputs, reporting readiness.
- AI agent (Ritchie) is additive and non-blocking: if the agent is unavailable, the backend continues to function normally.

## Core Backend
- Scaffold FastAPI with:
  - SQLAlchemy 2.x models.
  - Dual database engines in `core/database.py`: an async engine (asyncpg) with an async session factory for FastAPI request handlers, and a sync engine (psycopg2) with a sync session factory for Celery workers and Alembic. Workers never use the async engine.
  - Alembic migrations.
  - Pydantic schemas.
  - Postgres as canonical database.
  - PostGIS for map/geography queries.
  - `docker/postgres/init.sql` enables the `postgis` and `vector` extensions on first container start, before the first Alembic migration runs; `docker/minio/` init creates the default buckets on first startup.
  - Redis + Celery/RQ for background work.
  - Docker Compose for API, Postgres, Redis, and worker.
- Use a service-layer architecture:
  - Routers handle HTTP only.
  - Services enforce permissions, dedupe, AI write rules, and business logic.
  - Repositories isolate SQLAlchemy queries.
  - Background jobs handle Gmail sync, imports, AI extraction, geocoding, and agent event fanout.
- Auth:
  - Google OAuth login.
  - JWT/session handling after OAuth authentication.
  - Role model: `admin`, `managing_director`, `principal`, `analyst`, `agent` (scoped API key for Ritchie).
  - Role field exists for future use, but v1 does not have separate admin-only pages or human page-access restrictions.
- Documents:
  - Store metadata in Postgres.
  - Design for S3-compatible object storage.
  - Track external links, uploaded file metadata, source system, and related company/deal/person.
  - Local development can use a local storage adapter.

## Data Model
- Companies:
  - Startup/company profile, website, description, stage, sector, location, tags, primary company contact, Dealroom identifiers, canonical CRM fields, source provenance.
  - Manual company creation can start with only a company name; missing essential fields are shown as completeness gaps rather than blocking record creation.
  - V1 company completeness tracks website, description, sector, location, primary contact, relationship status, and tags.
  - Company completeness is exposed as both a percentage and a missing-field checklist.
  - Ritchie can directly fill low-risk company completeness fields when confidence is high, with source/confidence provenance.
  - Once a human edits a field, Ritchie can suggest or flag conflicting evidence, but cannot overwrite the human value unless that field is explicitly authorized for Ritchie in the runtime policy.
  - Deal diligence and rubric fields do not count toward company profile completeness because they belong to specific investment opportunities.
- People:
  - Founders, alumni, LP contacts, advisors, faculty experts, co-investors, operators.
- Company contacts:
  - A company can have multiple contacts, with one person marked as the primary contact for default workflows.
- Tags:
  - Company tags are hybrid: users can create tags during normal work, admins can merge/rename/archive tags, and protected system tags remain controlled for analytics.
  - Pass reason tags are required when marking a company/deal as passed.
- Affiliations:
  - RIT relationship, graduation year, college/program, founder/operator/investor/advisor/faculty roles.
- Interactions:
  - Emails, calls, meetings, notes, introductions, diligence conversations, relationship touchpoints.
- Deals:
  - A company can have multiple investment opportunities over time, including initial investments and follow-ons.
  - Each opportunity captures round details, relationship status, investment status, thesis fit, diligence status, co-investors, and decision notes.
  - Manual deal/opportunity creation requires a company and initial investment status; round details and funding stage are optional because 1829 often performs outbound alumni outreach before a company is actively fundraising.
  - Outreach targets and investment opportunities are explicitly distinguished so unanswered outbound messages do not count as active pipeline.
  - Initial investments and follow-ons use the same due diligence process and workflow gates.
  - Diligence is modeled with both stage-gated workflow status and checklist evidence, so the team can see where a deal is and which required diligence items are complete.
  - The 1829 screening rubric is a required diligence artifact for every deal opportunity, including follow-ons.
  - The rubric is the default evaluation framework for any company under consideration. The company detail view prominently surfaces the rubric from the active deal opportunity. If no opportunity exists yet, the company view provides a one-click path to create one and begin the rubric.
  - Knockout gates are binary pass/fail and must all pass before weighted scoring is recorded:
    - RIT Connection: founder, C-suite, or IP link to RIT?
    - Thesis Alignment: Photonics/Quantum, Clean Tech, Life Science, or Intelligent Systems?
    - Stage: Seed to Series A?
    - Tech-Enabled: proprietary IP or hard-tech barrier to entry? (No pure services/apps.)
  - Weighted scoring: each category scored 1 (Weak) to 5 (Exceptional), multiplied by its weight. Total is out of 100.
    - Team ("Builders"): ×5 (max 25). Sub-criteria: commercial/technical balance, coachability/grit, talent magnetism.
    - Tech ("Defensibility"): ×4 (max 20). Sub-criteria: IP protection, external validation, development stage.
    - Commercial ("Efficiency"): ×5 (max 25). Sub-criteria: capital efficiency, path to revenue, market pain, unit economics.
    - RIT Fit ("Leverage"): ×4 (max 20). Sub-criteria: structural advantage, talent pipeline, mission alignment.
    - Deal Dynamics: ×2 (max 10). Sub-criteria: syndicate strength, valuation discipline.
  - Score thresholds: 80–100 → move to deep diligence ("Head & Hands" winner); 70–79 → hold, assess fixability; below 70 → pass.
  - The data model stores individual sub-category scores (15 fields) and computes the composite automatically. Sub-category scores drive per-section breakdowns visible on the deal view.
  - Ritchie has a dedicated `vc-screening` skill that drafts rubric scores from pitch decks, intro emails, and Dealroom data. Rubric score writes are `blocked` in the authorization policy by default; Ritchie can only write drafted scores if the team explicitly authorizes the rubric tool. Drafted scores carry confidence and source provenance, and low-confidence sub-scores are flagged for human review. The rubric PDF (`planning/1829 Ventures Screening Rubric.pdf`) is the canonical reference for this skill. The rubric PDF (`1829 Ventures Screening Rubric.pdf` in the repo root) is the canonical reference for this skill.
- Funds:
  - First-class entity. Current funds: Beta and Fund I.
  - Fields: name, fund number/identifier, vintage year, committed capital, status (active/closed).
  - All investments reference the fund via foreign key — fund name changes propagate automatically to all associated investments without any backfill, since the name is stored once on the fund record and joined at query time.
  - Portfolio analytics (TVPI, DPI, IRR inputs) are calculated per-fund as well as across the portfolio.
- Investments:
  - Fund (foreign key to funds table), company, round, amount, investment date, instrument, valuation inputs, ownership snapshots.
- Portfolio metrics:
  - Revenue, runway, headcount, valuation marks, TVPI/DPI/IRR inputs, reporting period/date.
- Documents:
  - Email attachments, memos, pitch decks, data room references, object storage metadata, provenance metadata.
- Tasks:
  - First-class workflow objects for follow-ups, monitor reminders, diligence checklist work, assignments, and Ritchie-suggested next steps.
  - Tasks can be created manually or automatically from workflow events such as monitor dates, stale review-needed records, and Ritchie suggestions.
  - Tasks can be linked to companies, people, deals, interactions, imports, or agent proposals.
  - Tasks track one accountable owner, creator/source (human user, Ritchie, or system), optional watchers, due date, status, priority, and completion history.
  - Ritchie can directly create low-risk open tasks, clearly marked with Ritchie as creator/source.
  - Ritchie-created tasks default to the current user who triggered the event.
  - Users can reassign tasks to another owner.
  - Task notifications are sent to the current task owner.
  - Task reassignment notifies the new owner immediately, and the task is still included in that owner's daily digest if it remains open.
  - System-triggered tasks with no current user default to unassigned.
  - Unassigned tasks appear in a shared in-app/API queue and are not emailed to every user in v1.
  - Task notifications appear in-app/API and via email.
  - Multiple tasks due for the same user on the same day are bundled into a single daily email digest.
  - Daily task digests include overdue tasks, tasks due today, and an optional upcoming section for the next 7 days.
  - V1 task email digests send at 9:00 AM America/New_York.
- Imports and provenance:
  - Import batches, raw source rows, field-level source metadata, confidence, actor, timestamp.
- Deletion and archival:
  - Core entities (companies, people, deals, interactions, documents, tasks) are soft-deleted via an `archived_at` timestamp — never hard-deleted — so audit history, import provenance, and foreign keys stay intact.
- System audit log:
  - Every create, update, and archive across companies, contacts, deals, diligence, investments, rubric scores, statuses, tags, tasks, documents, and portfolio metrics stores actor, timestamp, old value, new value, and reason/context when available. Every change to the database is timestamped and logged, regardless of whether the actor is a human, an import, the system, or Ritchie.
  - Audit history is exposed both locally on company/deal pages and globally through an audit view. In v1, any authenticated human user can access the same pages.
- AI audit:
  - Agent actions, authorized writes, blocked attempts, source emails/documents/imports, rollback metadata.
- Agent event log:
  - Every event emitted to Ritchie: type, payload hash, timestamp, processing status, agent response summary.

## Roles and Permissions
- v1: all authenticated users have full access. No permission gates are enforced.
- Users have a `role` field (default: `member`) on the user record from day one — the column exists even though it isn't checked yet.
- All authenticated human users see the same pages in v1. There is no difference between an admin page and a normal user page for v1.
- Permission checks are centralized in a single `require_permission(user, action, resource)` guard in the API layer. In v1 this returns `True` for authenticated human users; adding a new role later means implementing the logic in one place, not hunting call sites.
- Planned future roles (not enforced in v1): `admin` (user management, fund settings), `analyst` (full pipeline CRUD, read-only on fund financials), `observer` (read-only).
- Google OAuth is the only login method. No username/password.
- V1 login eligibility is based on RIT Google accounts: a user must authenticate with a Google account whose email ends in an approved RIT domain, especially `@g.rit.edu`. This allows anyone with an RIT Google account to log in during v1.
- Future login eligibility will become invite-gated: a valid RIT Google email will still be required, but the user must also have a pre-existing invitation or approved account record before they can access the CRM.
- Accounts are created automatically on first successful eligible Google login in v1.
- The first-login/admin bootstrap flow is deferred unless needed for future role testing, because v1 does not distinguish admin and normal user page access.
- Ritchie authenticates to the CRM via a dedicated long-lived API key (not a Google OAuth session). Ritchie is only permitted to call `/agent/*` endpoints. All other routes reject Ritchie's key with 403. This is enforced at the API layer, not by network rules alone, so it holds regardless of deployment topology. Ritchie has no access to the codebase, database, or file system of the CRM host — it communicates exclusively through the defined API surface.

## 1829-Specific Fields
- Sector taxonomy:
  - Photonics, Imaging & Quantum.
  - Clean Tech & Energy.
  - Life Sciences & Health Tech.
  - Intelligent Systems, AI & Cyber.
  - Other.
- Thesis and diligence fields:
  - Screening rubric knockout gates: RIT connection, thesis alignment (Photonics/Quantum, Clean Tech, Life Science, Intelligent Systems), Seed-to-Series A stage, and tech-enabled/proprietary IP or hard-tech barrier.
  - Screening rubric weighted categories (1–5 scale, total /100): Team ×5, Tech ×4, Commercial ×5, RIT Fit ×4, Deal Dynamics ×2.
  - Score thresholds: 80–100 → deep diligence; 70–79 → hold; below 70 → pass.
  - 15 sub-category score fields stored individually; composite computed from them.
  - RIT source channel.
  - Faculty diligence involvement.
  - Alumni network connection.
  - Ecosystem engagement score.
  - Team score.
  - Scientific rigor score.
  - Validation/capital efficiency score.
  - Notes tying the company to 1829's investment thesis.

## Integrations
- Gmail:
  - Team members use separate Gmail accounts (personal or RIT). No individual OAuth per user.
  - The AI agent (Ritchie) has a dedicated Gmail address. Team members forward any email they want captured into the CRM to that address.
  - kernelbot already has a working Gmail IMAP IDLE listener (`docker/gmail/`) that watches Ritchie's inbox. No additional Gmail API work is required on the CRM backend side — kernelbot handles inbound email detection and enqueues a job when a forwarded email arrives.
  - When a forwarded email arrives, Ritchie parses the original email content from the forwarded message body, extracts sender, recipient, date, subject, and content, and attempts to match it to existing companies/people/deals via deterministic matching (email domain, known contact addresses) plus AI-assisted fuzzy matching.
  - Matched emails are stored as CRM interactions with provenance (forwarded by which team member, original sender/recipient, timestamp).
  - The raw forwarded message is always stored before any parsing begins. Parse failures (sender/subject/date/content extraction) route the email to the review queue just like match failures — an email is never silently dropped because a mail client formatted the forward unexpectedly.
  - Unmatched emails land in a review queue for a human to link manually.
  - Attachment metadata from forwarded emails is captured; attachments themselves are stored in MinIO if below a size threshold.
- Dealroom CSV:
  - The CSV export format (confirmed from `Dealroom Data (6.10.26).csv`) has rows 1–2 as Dealroom metadata (export URL and filter description); row 3 is the header row; data starts at row 4. The importer must detect and skip metadata rows before parsing headers.
  - Multi-value fields are semicolon-delimited within a single cell. Founders, funding rounds, investor names, tags, and industries all require splitting and parallel-array parsing.
  - Founders fields (`Founders`, `Founders universities`, `Founders linkedin`, `Founders statuses`, `Founders genders`) are parallel semicolon arrays — each index position represents one founder and maps to a People record.
  - Funding round fields (`Each round type`, `Each round amount`, `Each round currency`, `Each round date`, `Each round investors`) are parallel semicolon arrays — each index position maps to one funding round record.
  - Geography is pre-geocoded: `Latitude` and `Longitude` columns are present. PostGIS import is a direct coordinate load — no geocoding API call needed for Dealroom records.
  - Dealroom's `Industries`/`Sub industries` taxonomy must be mapped to 1829's 5-sector taxonomy (Photonics/Imaging/Quantum; Clean Tech & Energy; Life Sciences & Health Tech; Intelligent Systems, AI & Cyber; Other) during import. Unmapped industries default to Other and are flagged for review.
  - Upload CSV.
  - Support configurable column mapping.
  - Preview detected companies, founders, locations, duplicates, conflicts, mapped rows, and skipped rows.
  - Conflict review happens during preview before commit.
  - User commits the import batch.
  - Partial commit is allowed: clean rows can be committed while unresolved conflicts are skipped or preserved for later review.
  - Skipped and unresolved conflict rows remain visible in the import batch detail and do not create automatic tasks by default.
  - Newly created Dealroom-imported companies are marked `imported_unreviewed` until a human reviews or edits them.
  - `imported_unreviewed` is cleared only by an explicit human "mark reviewed" action, not by incidental edits.
  - `imported_unreviewed` companies appear in import, map, and search views by default, but are excluded from the main company-flow dashboard unless explicitly included by filter.
  - When marked reviewed, Dealroom-imported companies automatically enter the relationship lane as `identified`; users can change the status at any time.
  - Reviewed `identified` companies appear in the main company-flow dashboard by default and can be filtered out.
  - A company can move from `identified` to `contacted` through manual status change, a logged outreach interaction, or a sent/synced outbound email.
  - A founder/company reply automatically moves a contacted company to `review_needed`; users can manually correct the status if needed.
  - Entering `review_needed` automatically creates a triage task assigned to the user who sent/logged the outreach when known, otherwise unassigned, due the next business day.
  - Deduplicate by Dealroom ID, company domain, company name, founder email, and location.
  - Geocode city/state/country into PostGIS coordinates.
  - Store raw source row and import batch ID for auditability.
  - Never overwrite manually curated CRM fields or investment fields without explicit user action.
  - Dealroom imports can safely enrich empty fields and source metadata, but conflicts with curated CRM values require review in preview/conflict workflows.
- Custom AI agent (Ritchie / kernelbot):
  - Ritchie runs as **kernelbot** — a separate, self-contained multi-container Docker Compose stack in its own repo (`kernelbot_rit`). It must remain a separate repo and is not absorbed into the CRM backend.
  - kernelbot is TypeScript/JavaScript (Bun runtime) + bash scripts. It runs Claude Code CLI (`claude -p` one-shots per job), not the Anthropic Python SDK. It is not a Python service.
  - kernelbot already has: Gmail IMAP IDLE listener (watches Ritchie's inbox — the forwarding workflow is pre-built), Slack Socket Mode listener, Google Calendar poller, WhatsApp listener, a context-search MCP server (kernelbot-semble, Python, port 8077), and Airtable MCP for data storage. The CRM backend replaces the Airtable dependency.
  - v1 inbound integration: Gmail only. Google Calendar → interaction sync is deferred to v2 (same queue-driven pattern, additive change). WhatsApp is not used and will not be integrated.
  - Claude model: claude-sonnet-4-6 (already configured in kernelbot; routing to haiku for routine triggers is already in the queue protocol).
  - **Integration model:** The CRM backend exposes the `/agent` API endpoints as an **MCP server** — kernelbot is MCP-native, and one-shots call CRM tools via MCP (`mcp__crm__*`) rather than raw HTTP. A `"crm"` entry is added to kernelbot's `conf/mcp.json` pointing at the CRM's MCP endpoint. The MCP server uses the **Streamable HTTP transport** in v1 (SSE is deprecated in the MCP spec); the kernelbot `"crm"` entry is configured for streamable HTTP to match.
  - **CRM → kernelbot triggers:** When the CRM needs to trigger kernelbot (e.g., stale pipeline event, new import), the backend writes a JSON envelope to kernelbot's queue volume directly, or via a lightweight enqueue HTTP call.
  - **kernelbot → CRM writes:** kernelbot one-shots authenticate with the `agent`-role API key and call CRM MCP tools. Every write is attributed to Ritchie as a named actor.
  - Provide a dedicated `/agent` API with a scoped `agent`-role API key. Ritchie authenticates as a named actor — every write is attributable.
  - Agent can read permitted CRM/email/import context via structured query endpoints.
  - Agent uses a RAG context layer: a vector-indexed subset of CRM records (companies, interactions, deals) that Ritchie queries before acting, keeping context windows focused and costs predictable.
  - Agent can directly update trusted low-risk fields:
    - Company description.
    - Website.
    - Location.
    - Sector tags.
    - Founder/contact info.
    - Email-derived interaction summaries.
    - Source/provenance links.
  - Agent is blocked (default-deny) from writing the following unless a human explicitly authorizes the tool/field in the runtime policy:
    - Investment amount.
    - Valuation.
    - Ownership.
    - Deal stage/status.
    - Legal terms.
    - Investment recommendation.
    - Portfolio marks.
  - Every AI-created or AI-updated field stores confidence, source email/import/document, timestamp, and actor.
  - Blocked tool calls are rejected before any write occurs, logged as `policy_blocked` in the agent event log, and surfaced in agent analytics so the team can see what Ritchie attempted and decide whether to authorize that tool/field.
- All transactional notifications route through a single `NotificationService` abstraction. v1 delivers via SendGrid email only. Slack and any future channel are added by implementing a new channel adapter behind the same interface — no call-site changes required.
- v1 notification channels: SendGrid email (primary). Slack adapter slot reserved.
- In-app notification bell (frontend): planned but deferred to v2. The backend `notifications` table and delivery record will be designed from day one to support an unread-count and feed endpoint — the frontend bell is an additive UI layer that requires no schema migration when built.
- All transactional email (task digests, task assignment notifications) is sent via SendGrid (free tier: 100 emails/day) using SMTP relay on port 587. The SendGrid API key is stored as an environment variable.

## AI Agent Integration — Ritchie

This section defines the dev methodology for integrating Ritchie as a persistent, all-seeing agent over the 1829 Ventures backend. The goal: Ritchie can monitor everything, act where safe, and escalate where human judgment is required — with zero risk of silent data corruption.

### 1. Define Agent Capabilities as Explicit Typed Tools

Model every action Ritchie can take as a **typed tool definition** using the Anthropic tool-use API. Each tool has:
- A JSON Schema for inputs and outputs.
- An authorization tag: `authorized` (auto-execute) or `blocked` (rejected until a human updates the policy setting).
- An idempotency key field so retries never double-write.
- A configurable runtime policy so fields, tools, or actions can be moved between `authorized` and `blocked` without rewriting the integration; policy changes take effect immediately and are audited.

This forces a clean contract between the Claude layer and the backend service layer. The backend never evaluates free-form agent text — it only executes validated tool calls.

```
Tools (examples):
  update_company_description(company_id, description, source, confidence)  → authorized
  update_deal_stage(deal_id, new_stage, rationale)                         → blocked (default)
  create_interaction(company_id, summary, source_email_id, date)           → authorized
  flag_stale_relationship(company_id, last_interaction_date, note)         → authorized
  record_investment_recommendation(deal_id, recommendation, rationale)     → blocked (default)
```

### 2. Event-Driven Triggers — Backend Pushes to Ritchie

Rather than Ritchie polling, the backend **emits events** that the agent subscribes to. A background worker (Celery/RQ) fans out events to Ritchie's queue after key backend state changes:

- New Gmail thread synced and matched to a company.
- New Dealroom import batch committed.
- Deal stage has not changed in N days (stale pipeline alert).
- Portfolio metric reporting period opened.
- New company record created without sector tags or thesis fields.

Events are structured JSON envelopes: `{ event_type, entity_type, entity_id, payload, ts }`. The agent log table records every emitted event and its processing outcome.

This pattern means Ritchie is reactive and low-latency, not a cron-polling overhead.

### 3. Async by Default — Agent Never Blocks the Request Path

All agent operations run as **background jobs**. No synchronous Claude API call sits in a user-facing HTTP request. The flow is:

```
HTTP request → service layer → enqueue agent job → return 202 Accepted
                                      ↓
                             Celery worker → call Claude API → tool execution → audit log
```

This keeps API response times deterministic regardless of Claude API latency, and means Ritchie can process large context (long email threads, import batches) without timeouts.

### 4. Idempotent Writes — Safe Retries Everywhere

Every agent-initiated write includes an **idempotency key** (derived from event ID + tool name + entity ID). The service layer checks for an existing audit log entry with the same key before executing. Retries, queue re-deliveries, and agent restarts are all safe.

### 5. Immutable Audit Log Before Every Write

Before any agent write lands in the canonical tables, the service layer **records the intent** in the AI audit log:

```
{ actor: "ritchie", tool: "update_company_description", entity_id, old_value, new_value,
  source, confidence, idempotency_key, ts, status: "pending" }
```

The write is then executed and the log entry updated to `committed` or `failed`. This gives the team a complete, rollback-ready history of everything Ritchie has ever changed.

### 6. Binary Authorization Policy for Sensitive Changes

There is no per-change approval queue, proposal record, or email approval link. Every tool/field is either `authorized` or `blocked` in a runtime policy stored in the database:
1. Blocked tool calls are rejected at the policy gate before any service logic runs — they **never write to canonical tables**.
2. Each rejection is logged as `policy_blocked` in the agent event log with full context (tool, payload hash, rationale, confidence).
3. Blocked attempts are surfaced in agent analytics so the team can see what Ritchie tried and decide whether to authorize that tool/field.
4. A human can flip a tool/field to `authorized` at runtime; the change is audited, takes effect immediately, and a retried call then executes with its original idempotency key.

### 7. Search — Keyword + Semantic

Two complementary search modes, both backed by Postgres — no additional infrastructure.

**Keyword / full-text search** (`tsvector` + `GIN` index):
- Covers company name, founder name, notes, deal memos, interaction summaries.
- Powers the global search bar in the frontend: fast, exact/prefix matches.
- `tsvector` columns maintained via Postgres triggers; weighted by field importance (name > description > notes).

**Semantic / RAG search** (`pgvector` + HNSW index):
- Ritchie does not receive the entire database as context. Instead, the context-search layer retrieves the top-K most relevant records before each agent invocation.
- Also powers a "find similar companies" feature in the frontend for human users.
- Embedding model: `sentence-transformers` (`all-MiniLM-L6-v2`, 80 MB) running locally inside the Celery worker — free, no API key, no rate limits. Upgrade path to `all-mpnet-base-v2` (420 MB, higher quality) if needed.
- Records are embedded on write via a background Celery job. Vectors stored as pgvector columns on companies, interactions, and deal notes tables.
- `/agent/context` endpoint embeds the incoming query and returns top-K nearest neighbors via pgvector ANN search.
- Ritchie's system prompt is assembled dynamically: base identity + retrieved context + the triggering event.

Both indexes are updated asynchronously by Celery workers and never block writes.

### 8. Scoped API Key + Per-Endpoint Rate Limits

Ritchie authenticates with a long-lived scoped API key tied to the `agent` role. Rate limits are enforced per tool type by a small Redis token-bucket implemented in `api/middleware.py` — Redis is already in the stack, so no external rate-limit library is needed:
- Read endpoints: 120 req/min.
- Authorized writes: 60 req/min.

The key should be rotatable without a deploy. A dedicated admin-only panel is deferred.

### 9. Structured Outputs + Schema Validation

All Claude API calls use **structured output mode** (JSON Schema-constrained responses). The backend never parses free-form agent text into database writes. If the model's response doesn't validate against the expected tool output schema, the job fails cleanly and is retried or escalated — no partial writes.

### 10. Graceful Degradation

Ritchie is additive. If the Claude API is unavailable, rate-limited, or returns an error:
- Background jobs fail gracefully and are retried with exponential backoff.
- The event is logged as `agent_unavailable` — not silently dropped.
- No user-facing functionality is blocked.
- A daily health check reports agent job success/failure rates to the app/API. A dedicated admin-only panel is deferred.

### 11. Testing the Agent Integration

- **Unit tests**: mock the Claude API client. Assert that tool calls are constructed with correct schemas, idempotency keys are stable, and blocked tools never write.
- **Integration tests**: run a sandboxed agent endpoint against a test database. Fire real events, assert audit log entries, assert blocked tool calls are rejected and logged as `policy_blocked`.
- **Contract tests**: validate that every tool definition's JSON Schema matches the Pydantic model it maps to — run on every migration.
- **Replay tests**: record real agent job payloads in CI fixtures. Replay them to assert deterministic outcomes without live Claude API calls.

## API Surface
- `/auth`: Google login, refresh/session, current user.
- `/users`: internal users and role metadata for future permissions; no v1 page-access differences for human users.
- `/companies`: company CRUD, map fields, thesis fields.
- `/people`: people CRUD and RIT affiliations.
- `/interactions`: notes, meetings, emails, intros.
- `/deals`: pipeline, diligence, stage changes.
- `/investments`: investment records and ownership inputs.
- `/portfolio-metrics`: reporting and performance inputs.
- `/tasks`: follow-ups, monitor reminders, diligence work, assignments, and completion.
- `/imports/dealroom`: upload, preview, commit/run import, inspect errors.
- `/email/gmail`: connect account, sync mailbox, inspect/list synced threads, link emails to records.
- `/agent`: read context, submit authorized updates, read and update the runtime authorization policy.
- `/agent/context`: RAG context query endpoint — returns ranked relevant CRM records for a natural-language query.
- `/agent/audit`: read-only audit log of all agent actions and proposals.
- `/analytics`: pipeline, geography, source, sector, interaction, and portfolio dashboards.

## Analytics
- Pipeline analytics:
  - Main company-flow dashboard showing companies across relationship and investment stages, including review_needed.
  - Filtered stage dashboards for any company stage/status, such as review_needed, active diligence, monitor, or passed.
  - Deal pipeline by relationship status, investment status, sector, and source.
  - Outreach activity and active investment pipeline remain distinguishable in metrics even when shown in the same flow dashboard.
  - Stage conversion and stale opportunity detection.
- Geography analytics (deferred — post-v1):
  - Alumni founder/company pin map.
  - Location-based clustering by city, state, country, sector, and status.
  - Geo data (PostGIS coordinates) is stored from day one so this view can be built without a migration.
- Portfolio analytics:
  - Portfolio value inputs, TVPI/DPI/IRR inputs, markups, round history, and current status.
  - Portfolio company reporting snapshots.
- Relationship analytics:
  - Interaction cadence.
  - Stale relationship alerts.
  - Source and introduction tracking.
- Thesis analytics:
  - Thesis fit distribution across 1829's focus sectors.
  - RIT nexus and ecosystem engagement trends.
- Agent analytics:
  - Agent job success/failure rates.
  - Trusted write volume by tool and entity type.
  - Blocked attempt volume by tool and entity type.
  - Context query latency and token usage trends.

## Test Plan
- Continuous integration: a GitHub Actions workflow (`.github/workflows/ci.yml`) runs ruff, mypy, backend tests with coverage, and frontend lint/typecheck/tests on every push and pull request.
- Code coverage:
  - Track code coverage as part of the test workflow.
  - Backend Python coverage should use `coverage.py` through `pytest-cov`.
  - Frontend TypeScript coverage should use Vitest coverage with the V8/Istanbul provider.
  - JaCoCo is not planned unless a Java/JVM component is added later.
- Unit tests:
  - Auth roles and permission boundaries, including the `agent` role.
  - Dealroom CSV parsing, column mapping, preview, dedupe, non-overwrite rules, and commit behavior.
  - Manual CRM fields winning over imported data.
  - AI authorized writes vs blocked writes (policy gate enforcement).
  - Gmail message normalization and record matching.
  - Portfolio metric calculations.
  - Agent tool schema construction and idempotency key stability.
  - Blocked tools never write to canonical tables.
- Integration tests:
  - Full Dealroom CSV upload, parse, dedupe, and commit flow.
  - Gmail sync-to-interaction flow.
  - AI extraction-to-company-update flow.
  - Company-centered CRM workflow across people, interactions, deals, and investments.
  - Deal pipeline CRUD and analytics endpoints.
  - Alembic migration creation and rollback on a test database.
  - Agent event fanout: emit event → background job → tool execution → audit log entry.
  - Authorization policy flow: blocked tool call rejected and logged → human authorizes the tool at runtime → retried call executes with the original idempotency key.
  - Agent context query endpoint returns ranked relevant records.
- Acceptance scenarios:
  - Import a Dealroom CSV and view parsed, deduped company and founder records.
  - Sync a Gmail thread and link it to the correct company.
  - Let the AI update a trusted company field with provenance.
  - Confirm the AI cannot directly modify valuation, ownership, legal terms, investment recommendation, portfolio marks, or investment amount.
  - Query dashboard data for pipeline, sector focus, source breakdown, portfolio performance inputs, and founder geography.
  - Stale pipeline event triggers agent job; agent flags the deal; audit log records the action.
  - Flip a blocked tool to authorized at runtime and confirm the change takes effect immediately, without restart, and is audited.
  - Rotate Ritchie's API key and confirm old key is immediately invalid.
  - Restore the database from the latest nightly backup onto a clean Postgres container.

## Deployment
- **v1 (proof of concept):** Everything runs locally on the personal Ubuntu 24.04 VM (6 GB RAM) via Docker Compose. All data stored locally — Postgres on VM disk, MinIO on VM disk. No external cloud services required. Accessed via SSH / local network.
- **Backups (required from day one):** a nightly `pg_dump` (cron or a lightweight compose service running `backend/scripts/backup_db.sh`) writes compressed dumps to a backups directory, retains the last 14 days, and copies each dump off the VM (free-tier object storage or a synced drive). The MinIO data directory is included in the same nightly copy. A restore from backup is tested once as a v1 acceptance step.
- **v2:** Proper deployment procedures — domain, SSL, external object storage (Cloudflare R2), potential migration to RIT server or cloud host. All deferred.
- **Deployment-agnostic design principles** (applied throughout so v2 migration requires only env var changes, not code rewrites):
  - All config via environment variables — no hardcoded hostnames, ports, credentials, or paths.
  - Backing services (Postgres, Redis, MinIO) referenced only by connection string env vars.
  - Stateless API containers — no local disk state, no in-process session storage.
  - Object storage via S3-compatible interface only — MinIO in v1, Cloudflare R2 (10 GB free, zero egress) or equivalent in v2, swapped with one env var change.
- Memory budget on the VM (approximate): Postgres ~512 MB, FastAPI workers ~256 MB, Celery worker (including the sentence-transformers model) ~1 GB, Redis ~64 MB, MinIO ~256 MB — total ~2.1 GB, leaving roughly 4 GB headroom on the 6 GB VM.
- Frontend: React + Vite, TypeScript, shadcn/ui component library (Tailwind CSS under the hood). Served as a static build by nginx. Nginx proxies `/api/*` to FastAPI and serves the frontend at root (`/`).
- Frontend lives in `frontend/` at the repo root. It is built with `vite build` and the output (`dist/`) is served by nginx. The Docker Compose setup includes a `frontend` service for local dev (Vite dev server with HMR) and the nginx service handles production serving.
- State management: React Query (TanStack Query) for server state — no Redux. Forms handled with React Hook Form + Zod for client-side form validation only.
- Frontend domain types are generated from the FastAPI OpenAPI spec via `openapi-typescript` from day one — an npm script regenerates them whenever the API changes. Hand-written TypeScript mirrors of Pydantic schemas are not maintained.
- Authentication flow: frontend redirects to Google OAuth, receives JWT from the API on callback, stores it in `httpOnly` cookie (not localStorage).
- Key v1 views: pipeline board (Kanban by deal status), company detail (logically organized company information + fillable active rubric + interaction history), contact detail, portfolio dashboard, task list, import/CSV management, Ritchie activity view (agent audit log + authorization policy toggles).
- Frontend company detail requirement: near the end of v1, when the frontend is being built, the company page should become the main workspace for reviewing a company. It should display company information in a logical layout and include an in-page screening rubric that users can fill out without leaving the company page.
- Pipeline board default columns (in order): Outreach → Intro Meeting → Initial Review → Diligence → IC Review → Term Sheet → Closed/Invested. Passed deals appear in a separate swimlane below the main board.
- Deal statuses are a configurable list stored in the database (not hardcoded enums), so new stages can be added and reordered later without a code change. In v1, no separate admin-only page access is required for this.

## Assumptions
- LP portal, founder portal, and full fund accounting are deferred.
- Carta is a benchmark for fund CRM and portfolio workflows, not a v1 integration.
- Google OAuth is used for login. A new Google Cloud project must be created specifically for the 1829 Ventures CRM (separate from kernelbot's Google credentials). Required setup: OAuth 2.0 client ID, authorized redirect URIs, app in testing mode with team members added as test users for v1. The Google People API must be enabled for profile info on login. V1 accepts eligible RIT Google accounts, especially emails ending in `@g.rit.edu`; future versions will require both an eligible RIT Google email and an invitation/approved account record.
- Dealroom integration is CSV-based, not API-based.
- Postgres/PostGIS is required because geography and map analytics are core product features.
- Object storage: MinIO (self-hosted, S3-compatible) for v1 — runs as a Docker Compose container, stores files on VM disk. Cloudflare R2 targeted for v2 (10 GB free forever, zero egress fees). Interface is identical — swap is one env var change.
- Users can upload documents (pitch decks, memos, attachments) directly from the company detail page via drag-and-drop. The API issues a presigned upload URL; the frontend uploads directly to storage without proxying through the API server.
- Transactional email is sent via SendGrid free tier (100 emails/day). The SendGrid API key is an environment variable; no self-hosted mail server is required.
- Funds are a first-class entity; Beta and Fund I are the two current funds. Fund name changes propagate automatically via foreign key join.
- The CRM is a fresh start. No data migration from Airtable or any other system. The Dealroom CSV is the primary seed dataset.
- Ritchie (the AI agent) is a named, authenticated actor in the system from day one — not bolted on later.
- All Claude API calls are async background jobs; no synchronous agent calls in the user-facing request path.
- The RAG context layer (vector index) is required for cost-controlled, focused agent context — full-table context is not used.
- The `agent` role API key should be rotatable without a deploy. A dedicated admin-only panel for this is deferred.
- Production deployment uses Docker Compose on an RIT Linux server; nginx handles SSL termination and reverse proxying.

## Build Sequence

Solo AI-assisted build (3 hours/day) targeting June 30 operational date (20 days from June 10). Backend first, then frontend. With AI code generation, the bottleneck is architectural decisions — not writing boilerplate. The Dealroom CSV is already in the repo. Ritchie is already built and needs configuration, not construction.

### Phase 1 — Backend (Days 1–17)
- Days 1–3: Scaffold — Docker Compose, FastAPI, Postgres/PostGIS with pgvector, Alembic, Google OAuth + JWT, role model, MinIO.
- Days 4–7: Core data models + migrations + CRUD — funds, companies, people, affiliations, deals, interactions, tasks, investments, portfolio metrics, documents, tags, screening rubric (15 sub-scores + computed composite).
- Days 8–10: Pipeline workflow logic — relationship/investment status transitions, configurable deal statuses, review_needed triage, pass/monitor/start-review outcomes, diligence checklist.
- Days 11–13: Dealroom CSV import — column mapping, preview, dedupe, conflict resolution, geocoding, commit.
- Days 14–15: Gmail forwarding ingestion — poll Ritchie's inbox, parse forwarded email, match to CRM records, create interactions. Document upload via presigned MinIO URLs.
- Days 16–17: Tasks + SendGrid notifications — assignment, daily digest, due-date reminders, approval proposal emails with signed approve/reject links. Keyword search (tsvector + GIN) + semantic search (pgvector HNSW + sentence-transformers). Analytics endpoints (pipeline, portfolio, source, sector).

### Phase 2 — Ritchie Integration (Days 17–18, parallel track)
- Configure `/agent/*` endpoints as MCP server, scoped API key, tool definitions, event fanout, RAG context layer.
- Add `"crm"` entry to kernelbot `conf/mcp.json`. *(Can start earlier if kernelbot review happens in parallel.)*

### Phase 3 — Frontend (Days 18–20)
- Days 18–19: Core views — pipeline board (Kanban), company detail (logical company profile + fillable rubric + interactions + documents), contact detail, task list, Ritchie activity view (audit log + policy toggles).
- Day 20: Auth flow (Google OAuth callback, httpOnly cookie), import/CSV management UI, portfolio dashboard, smoke test end-to-end on VM.

## Potential Future Features
- Automated ranking order for companies based on investment-fit score, confidence/completeness, relationship access, and other prioritization signals.
- Deal owner assignment and owner-based pipeline analytics for a larger team.
