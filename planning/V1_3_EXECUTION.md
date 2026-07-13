# v1.3 Execution Plan And Acceptance Criteria

This is the implementation companion to `PLAN_v1.3.md`. It narrows the feature inventory into independently releasable work, keeps security-sensitive work explicit, and records dependencies that cannot responsibly be guessed in code.

## Delivered In This Change

| Area | Delivery | Acceptance criterion |
| --- | --- | --- |
| Profile editing | Company and person Save/Cancel forms with API validation and cache invalidation. | A user changes a company and person field; the persisted detail view refreshes and the existing audit service records the change. |
| Documents | Direct-browser upload, storage size policy, byte/MIME confirmation, download URL, archive, and company/person drop zones. | An allowed file becomes `confirmed` only after server confirmation; disallowed/oversize uploads become `rejected` and are removed from storage. |
| Outreach | Interaction fields for channel, direction, follow-up state, creator, filters, and a manual outreach view. | A logged outbound touch appears chronologically, filters by channel/owner/follow-up, and affects cooldown logic. |
| Candidate queue | Derived, explainable ranking with status/confidence, stage, fit, evidence, and recency factors. | A verified operational Seed company with an active RIT founder ranks above an otherwise comparable uncertain company; score reasons and warnings are visible. |
| Agent/MCP | Document listing, outreach logging, enrichment update, and candidate-list tools. | Each new MCP write is subject to the current policy and creates normal audit records. |

## Release Gates

1. Apply migrations through `e6f1a4b3c8d2` on a disposable database and verify a downgrade/upgrade cycle.
2. Run backend ruff, mypy, unit/integration tests, and frontend lint/typecheck/tests/build.
3. Smoke test direct browser upload against MinIO with `S3_ENDPOINT_URL` set to the container endpoint and `S3_PUBLIC_ENDPOINT_URL` set to the browser endpoint.
4. Confirm rejected upload cleanup, archive behavior, and five-minute download URLs.
5. Confirm an MCP identity cannot call a blocked tool after policy refresh.

## Deliberately Deferred Dependencies

- **Saved candidate lists, per-item assignment, and status automation:** require a durable candidate-list model and product decisions for refresh/merge semantics. The current queue is derived and read-only so it cannot silently overwrite team work.
- **LinkedIn message memory:** a read-only, authorized source path (export or approved connector) is required. No code should scrape LinkedIn or imply access that is not granted.
- **Automatic follow-up tasks from LinkedIn:** waits on that source path and a stable message provenance model. The existing task model already supports agent provenance.
- **Rubric/thesis document parsing:** the supplied source documents remain the source of truth, but automated extraction/versioning requires a supported parser plus an explicit refresh policy. The current score fields preserve provenance and enable manual/MCP enrichment safely.
- **News aggregation:** remains outside the mini-sprint.

## Review Principles

- Prefer one model for interactions/outreach rather than a parallel activity log.
- Never treat passive verification, scoring, or enrichment as a human relationship touch.
- Keep uncertainty visible; `unclear` and `unverified` receive warnings and score penalties rather than false certainty.
- Keep the browser, API, storage, and MCP permissions separate. A working UI must not become an authorization bypass.
