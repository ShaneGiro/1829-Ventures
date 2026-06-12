# Agent 09: Gmail Ingestion

## Goal

Implement the forwarded-email ingestion pipeline: kernelbot notifies the CRM when a forwarded email arrives in Ritchie's inbox; the CRM parses the forwarded message, matches it to companies/people/deals, stores it as an interaction with provenance, and routes failures to a review queue.

## Read First

- `planning/PLAN_v1.md` (Gmail sections under Integrations and Main User Workflows)
- `planning/FILE_STRUCTURE.md`
- `planning/APP_WORKFLOW_AND_FILES.md`
- `.agents/README.md`

## Depends On

- `02_MODELS_MIGRATIONS.md`
- `04_CORE_CRM_API.md`
- `07_DOCUMENTS_TASKS_NOTIFICATIONS.md` (storage abstraction for attachments)

## May Edit

- `backend/app/api/routes/email.py`
- `backend/app/services/gmail_ingestion_service.py`
- `backend/app/workers/jobs/gmail_jobs.py`
- `backend/app/repositories/interactions.py`
- Email/interaction schemas if missing fields are discovered.
- Gmail ingestion tests (`test_gmail_ingestion.py`).

## Avoid

- Gmail API/IMAP work — kernelbot owns inbox watching; the CRM only receives notifications.
- Ritchie tool execution behavior (Agent 10).
- Dealroom import.
- Frontend.

## Expected Output

- The raw forwarded message is always stored before any parsing begins.
- Forwarded-message parsing extracts original sender, recipient, date, subject, and content.
- Parse failures route the email to the review queue exactly like match failures — an email is never silently dropped because a mail client formatted the forward unexpectedly.
- Deterministic matching (email domain, known contact addresses) runs before AI-assisted fuzzy matching.
- Matched emails become CRM interactions with provenance: forwarding team member, original sender/recipient, timestamp.
- Unmatched emails land in a review queue for manual linking.
- Attachment metadata is captured; attachments below the size threshold are stored via the storage abstraction (MinIO in v1).
- A founder/company reply moves a contacted company to `review_needed` per the pipeline rules (coordinate with Agent 05's transition hooks — call the pipeline service, do not reimplement transitions).
- Secondary processing (embedding the interaction, triggering tasks) is enqueued as background jobs.

## Tests To Add Or Run

- `test_gmail_ingestion.py`: forwarded-email parse for at least two forward formats (Gmail web, Outlook-style), parse-failure routing, deterministic match, unmatched review queue, attachment threshold.
- Provenance assertions: forwarding user and original sender are both recorded.

## Definition Of Done

- A forwarded email payload can flow end-to-end in a test: receive → store raw → parse → match → interaction created with provenance.
- Parse and match failures are reviewable, never dropped.
- No synchronous slow work in the request path — heavy processing is in workers.
