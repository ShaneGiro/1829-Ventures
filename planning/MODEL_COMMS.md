# Model And Integration Contracts

## Ownership Boundaries

- The React client talks only to the versioned FastAPI API under `/api`; it never connects directly to Postgres, Redis, MinIO, Gmail, LinkedIn, or an LLM provider.
- FastAPI routes authenticate and authorize, schemas validate the wire contract, services enforce workflow rules and auditing, and repositories own SQLAlchemy queries.
- Browser document bytes go directly to S3-compatible storage only after the API creates a constrained presigned POST. The API confirms the landed object by checking its size and sniffing its bytes before making metadata downloadable.
- MCP is the sole kernelbot/Ritchie integration boundary. MCP tool handlers invoke the same service/repository paths and audit/policy gate as REST workflows.

## Write And Audit Flow

```text
User / MCP tool → API policy guard → Pydantic schema → service → repository/model
                                      │                         │
                                      └──── audit event ◀────────┘
```

All human and agent writes must preserve this flow. Agent tools must not issue direct SQL or bypass the runtime `authorized`/`blocked` policy.

## External-System Boundaries

| System | Permitted v1.3 behavior | Explicitly excluded |
| --- | --- | --- |
| Object storage | direct upload/download through short-lived presigned URLs | API-proxied file bytes; automatic hard delete |
| Email | explicitly copied/Bcc-to-Ritchie messages | broad inbox OAuth, mailbox sync |
| LinkedIn | future read-only export/connector ingestion | sending, deleting, read-state mutation, hidden scraping |
| Calendar | no v1.3 integration | read/sync/write access |
| Ritchie/kernelbot | typed MCP tools constrained by CRM permissions | privileged backdoor access |

## Candidate Signals

Candidate ranking is intentionally explainable and versioned. Verification data stores status, confidence, evidence, verifier timestamp, and score reasons separately from relationship activity. Passive enrichment must never change the last-outreach timestamp.
