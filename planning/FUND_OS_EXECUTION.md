# RIT Fund OS Implementation Ledger

Last updated: July 13, 2026

## Status

Implementation has started. The first foundation slice is complete and verified; the full product roadmap is not yet implemented.

## Delivered in the first slice

### RIT organization and legal-entity foundation

- Added an RIT-owned organization boundary and automatic membership provisioning for authenticated RIT users.
- Added legal entities and effective-dated parent, manager, administrator, and related-entity relationships.
- Scoped funds to an organization and optionally to a legal entity.
- Added audited organization and legal-entity APIs.
- Added a fund-operations permission matrix while preserving current CRM behavior.

### Financial correctness foundation

- Added strict `Decimal` money parsing, quantization, fixed-point serialization, and deterministic largest-remainder allocation.
- Rejects floats, booleans, NaN, and infinity at financial boundaries.
- Added seeded allocation and edge-case tests.

### Outreach workflow foundation

- Added durable, user-owned candidate lists with assignees, statuses, score snapshots, duplicate prevention, and append-only change history.
- Preserved the existing derived outreach queue while adding saved-list APIs.

### Portfolio transition safety

- Removed synthetic returned-capital, DPI, TVPI, RVPI, IRR, and XIRR values from the portfolio dashboard.
- Relabeled legacy marks so estimates are not presented as reconciled financial facts.
- Added a prominent warning that portfolio values are not yet reconciled to Workday.

### Platform integration and hardening

- Added and validated forward-and-back database migrations for the organization and outreach foundations, including a merge migration.
- Regenerated the frontend API contract and TypeScript client types.
- Fixed null metadata handling in rejected document uploads.
- Made forwarded-email ingestion direction and follow-up defaults explicit.

## Verification completed

- Backend unit tests: 146 passed.
- Backend integration model tests: 5 passed.
- Python lint: passed.
- Python static type checking: passed across 151 source files.
- Database migration downgrade and upgrade cycle: passed.
- Frontend lint: passed.
- Frontend type checking: passed.
- Frontend tests: 8 passed.
- Frontend production build: passed.

The full backend suite was run with the repository's documented RIT domains (`g.rit.edu,rit.edu`) and the existing Dealroom reference export made available inside the test container.

## Not yet implemented

- Carta CSV/Excel ingestion, staging, validation, and exception resolution.
- Normalized securities, investment transactions, valuations, exits, and ownership history.
- Workday export/import connector, account mappings, reconciliation workflow, and close controls.
- Fund performance calculations backed by imported and reconciled transactions.
- Frontend screens for saved outreach lists and organization/legal-entity administration.
- Accountants' and administrators' review workspace.
- Document retention, institutional audit reporting, SSO/identity lifecycle hardening, and production deployment controls.

## Recommended next slice

1. Collect representative Carta exports and define a versioned import manifest without importing production data yet.
2. Implement normalized portfolio-company, security, transaction, valuation, and ownership-ledger models using the new decimal conventions.
3. Add staged Carta imports with row-level validation, idempotency, provenance, and an exception queue.
4. Build the saved outreach-list interface on the APIs delivered in this slice.
5. Conduct Workday integration discovery with RIT's finance/IT owner to define supported interfaces, chart-of-accounts mappings, close cadence, and reconciliation ownership.

Fund-term-dependent calculations remain provisional until governing terms or an approved calculation policy are available; the absence of an LPA should not be silently replaced with assumptions.
