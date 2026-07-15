# PRD — Meridian: Venture Fund CRM

## Original problem statement
> A CRM/database to store and track conversations, diligence items, and investments for a new Venture Fund.

## User choices (confirmed)
- Auth: JWT email/password
- Entities: Companies, Contacts, Conversations, Diligence, Investments, Portfolio metrics per fund (Beta, Fund I)
- AI: no AI features for now — user will connect their own AI agent later
- Design: Bloomberg/Carta-style dark, finance-grade
- File uploads: not needed

## Architecture
- Backend: FastAPI + Motor (async MongoDB), bcrypt + PyJWT httpOnly cookie auth
- Frontend: React 19 + React Router 7, TailwindCSS, shadcn/ui (radius overridden to 0), Chivo/Inter/JetBrains Mono, Phosphor Icons
- All API endpoints under `/api`; cookies `samesite=none; secure` for cross-origin preview URL

## Personas
- Fund GP / Partner: sources, tracks diligence, closes investments
- Analyst: logs conversations, maintains checklist
- Operations: portfolio-level reporting per fund

## What's been implemented (2026-02)
- Multi-user JWT auth (register, login, logout, refresh, brute-force lockout, admin seeding)
- Two funds seeded: Beta Fund, Fund I
- Companies CRUD + pipeline stages (sourced → screening → diligence → IC → invested → passed)
- Company detail with 5 tabs: Overview, Conversations, Diligence, Investment, Contacts
- Conversations log (date, channel, attendees, summary, next steps, sentiment)
- Diligence checklist by category (Legal, Financial, Tech, Market, Team) with status pills
- Investment records (amount, round, valuation, ownership %, close date, board seat, pro-rata, current mark)
- **Cash-flow schedule per investment** (capital calls + distributions with add/remove)
- **Fund-level XIRR** computed via Newton's method over all investment cash flows
- Contacts CRM (founder / co-investor / LP / advisor) linked to companies
- Portfolio metrics: deployed capital, dry powder, MOIC, **IRR**, investments count, pipeline & sector breakdown
- Global ⌘K search across companies, contacts, conversations
- **Inline-edit company sidebar fields** (sector, round, ask, HQ, website, lead partner, source)
- **Dealroom.co CSV import** — upsert-by-name mapping (Name, Website, Tagline, Long description, Industries, HQ, Growth Stage → pipeline stage, Last round/amount, Founders, Investors, Total funding, Valuation, Dealroom profile URL)
- **Companies search + pagination** (50/page, real-time client filter)
- **LP report CSV export** — /api/export/lp-report streams a per-fund CSV with company/round/amount/valuation/ownership/close-date/current-value/MOIC/IRR
- Dark Swiss/Bloomberg-inspired UI (rounded-none, monospace data columns, sharp borders)

## Backlog (P0 → P2)
- P1: AI agent integration hooks (webhooks or MCP endpoints for the user's external agent)
- P1: PDF export for LP reports (currently CSV only)
- P1: File uploads for pitch decks & term sheets (deferred by user)
- P2: LP portal / capital call notifications
- P2: Board reporting exports
- P2: Email/calendar integration for conversation auto-logging

## Test credentials
See `/app/memory/test_credentials.md` (admin@fund.com / admin123)
