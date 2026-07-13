# 1829 Ventures CRM — v1.3 Plan

## Summary

v1.3 is the next release after v1 (see `planning/PLAN_v1.md`). This document is the working plan for v1.3 and will grow as additional v1.3 features are scoped — each feature gets its own subsection under the shared headings below (Data Model, API Surface, Frontend, Test Plan, Build Sequence) so the document stays organized by concern rather than by feature, matching `PLAN_v1.md`'s structure.

**Mini-sprint scope:** v1.3 should make the CRM feel operational instead of read-only. The priority is editing company/founder profiles, dropping documents directly onto those profiles, tracking outreach activity, keeping the MCP server current with product changes, and preparing Ritchie/kernelbot to interact with the CRM through that MCP layer.

**Primary features in scope:**
- Editable company profiles.
- Editable founder/person profiles.
- Drag-and-drop documents on company and founder/person profiles.
- Outreach tracking: a dedicated place to see everyone we've reached out to and when.
- RIT alumni founder verification for outreach list building: Ritchie checks whether the Dealroom-identified RIT alumni founder still appears active at the company.
- Operational status verification for outreach list building: Ritchie checks whether a company appears to still be operating instead of trusting Dealroom's active/inactive flag by itself.
- Outreach Candidates: a working list builder for companies that match the current RIT alumni founder, operational, and pre-seed to Series A target segment.
- Thesis/rubric-aware candidate scoring: candidates rank higher when they score well against `reference_files/"1829 Ventures Screening Rubric.pdf"` and align with `reference_files/"1829 Ventures Investment Thesis v2.7.docx"`.
- LinkedIn message memory: a read-only workflow that combs through the user's LinkedIn messages to organize companies/people already interacted with so follow-up context is not forgotten.
- Email memory stays limited to Ritchie's existing Bcc workflow; no broad Gmail/inbox access in v1.3.
- Continuous MCP server updates as CRM capabilities change.
- Ritchie/kernelbot integration through the MCP server, limited by the same permission model as the CRM.

**Future consideration, not a v1.3 priority:** a News tab that aggregates news related to portfolio companies.

## Mini-Sprint Priorities

1. **Profile editing:** users can update company and founder/person profile fields from the UI without using scripts, seed data, or direct API calls.
2. **Profile document drop:** users can drag files onto a company or founder/person profile and later download/archive those files.
3. **Outreach tracking:** users can see a consolidated record of who has been contacted, when, about what, and by whom.
4. **RIT alumni founder verification:** users can identify companies that have an RIT alumni founder who still appears active at the company, with confidence and evidence visible on the company profile.
5. **Operational status verification:** users can filter outreach candidates by whether Ritchie believes the company is still operating, with confidence and evidence visible on the company profile.
6. **Outreach Candidates:** users can generate and work through a saved list of companies that match the current target segment, assign owners, and log outreach from the list.
7. **Thesis/rubric-aware scoring:** outreach candidates are ranked by fit against the 1829 screening rubric and investment thesis, with explainable score reasons.
8. **LinkedIn message memory:** users can see companies and people they have already interacted with in LinkedIn messages, organized for follow-up and linked back to CRM records where possible.
9. **MCP freshness:** the MCP server stays aligned with recent backend/frontend changes and exposes the new profile, document, outreach, candidate-list, scoring, LinkedIn-memory, alumni-verification, and operational-verification capabilities as they land.
10. **Ritchie/kernelbot access:** Ritchie uses the MCP server as its integration boundary and can interact with records, documents, outreach workflows, candidate lists, scoring, LinkedIn message memory, alumni-founder verification, and operational-status verification only where permissions allow.

## Current State — File Storage (as of v1.2)

v1 partially scaffolded file storage but never finished it. This is the actual state of the code today, not the aspiration in `PLAN_v1.md`:

**What exists and works:**
- `Document` model (`backend/app/models/document.py`): metadata in Postgres — `filename`, `content_type`, `size_bytes`, `storage_key`, `external_link`, `source` (`upload`/`email`/`dealroom`/`external_link`), links to `company_id`/`deal_id`/`person_id`, `uploaded_by`, `extra_metadata` JSONB, soft-delete (`archived_at`).
- MinIO runs as a Docker Compose service (S3-compatible), with a `crm-documents` bucket auto-created on startup (`docker/minio/init.sh`).
- `DocumentStorage` protocol (`backend/app/integrations/storage.py`) with a MinIO implementation (`minio_storage.py`) using `boto3`.
- Full CRUD on document *metadata*: `GET/POST /documents`, `GET/PATCH /documents/{id}`, `POST /documents/{id}/archive`.
- `document_service.create_presigned_upload` creates a `Document` row and asks MinIO for a presigned upload URL.

**What is broken or missing — this is the real gap v1.3 closes:**
1. **The upload flow does not actually work.** `MinioDocumentStorage.create_presigned_upload` calls `boto3`'s `generate_presigned_post`, which returns both a `url` and a `fields` dict (policy, signature, and any required form fields). The adapter discards `fields` and only returns `url` (`PresignedUpload` dataclass has no `fields` attribute). A client cannot complete a presigned POST to S3/MinIO without those fields — the request will be rejected. **No file has ever been successfully uploaded through this path.**
2. **There is no download endpoint.** No route, service method, or storage method returns a way to retrieve a stored file. Metadata can be listed; bytes cannot be fetched.
3. **There is no frontend upload UI at all.** `frontend/src/api/documents.ts` only has a read-only `useDocuments` hook. No dropzone, no file picker, no upload mutation exists anywhere in the frontend.
4. **The frontend document list is inert.** `CompanyDetail.tsx` renders `documents.items.map(d => d.filename)` as plain text — no icon, no size, no download link, no delete action.
5. **No server-side validation.** `PresignedUploadRequest` accepts client-declared `content_type` and `size_bytes` at face value; nothing checks the real object after upload, nothing enforces an allowed file-type list or a max size.
6. **Documents are invisible to search.** The keyword/semantic search layer described in `PLAN_v1.md` §7 covers companies, interactions, and deal notes — not documents. Filenames and file contents are not searchable.
7. **`put_object` (trusted server-side write, used by the Gmail attachment path) works today** — it's the presigned client-direct path that's broken. Any future Gmail-attachment work is unaffected by this gap.

## Key Product Decisions — File Storage

- Keep the existing architecture: metadata in Postgres, bytes in S3-compatible object storage (MinIO in v1/v1.3, swappable to Cloudflare R2 in v2 via env var only — no code change). Fix the broken presigned-POST flow rather than replacing it with a proxy-through-API upload, to preserve the "frontend uploads directly to storage, API never proxies file bytes" principle from `PLAN_v1.md`.
- Documents attach to a company, deal, and/or person, exactly as today. The v1.3 UI priority is company and founder/person profile attachments. Deal-level reuse is allowed if the component boundary is cheap, but it is not the sprint driver. Task-level attachments are out of scope for v1.3 (see Potential Future Features).
- Allowed file types (extension + verified MIME/magic bytes, not just the client's declared `Content-Type`):
  - Documents: `.pdf`, `.md`, `.markdown`, `.txt`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.csv`.
  - Images (decks/screenshots/cap-table exports are often pasted as images): `.png`, `.jpg`, `.jpeg`.
  - The allowlist lives in one place (`app/core/constants.py`, `ALLOWED_DOCUMENT_EXTENSIONS`/`ALLOWED_DOCUMENT_MIME_TYPES`) so it can be extended without touching route/service code.
- Max upload size: 50 MB per file by default, configurable via `S3_MAX_UPLOAD_MB` env var. Large enough for a full pitch deck or data-room PDF; small enough that a 6 GB VM with a self-hosted MinIO doesn't get filled by a stray video upload. The presigned POST must include a `content-length-range` condition so oversized files are rejected by storage before the upload completes, not only after confirmation.
- Browser-direct uploads need two endpoint concepts in local/Docker development: the API signs against the internal MinIO endpoint, but the browser must receive a public/browser-reachable URL such as `http://localhost:9000`. Add an env-driven public storage endpoint (for example `S3_PUBLIC_ENDPOINT_URL`) or equivalent response rewriting, and configure MinIO bucket CORS for the frontend origin.
- **Server verifies what actually landed in storage**, not what the client claims. After the browser completes the presigned POST, the frontend calls a new confirm endpoint; the backend reads object metadata for the real size and fetches a small ranged prefix of object bytes for magic-byte content sniffing, then rejects and deletes the object if it's oversized or not an allowed type. A plain S3 `HeadObject` is not enough for MIME sniffing because it does not return object bytes.
- Archiving a document soft-deletes the metadata row only (`archived_at`), consistent with the "never hard-delete" audit principle in `PLAN_v1.md`. The underlying object stays in MinIO. A `delete_object` capability is added to the storage protocol for a future explicit retention/purge job, but v1.3 does not call it automatically.
- Download is via a short-lived presigned GET URL (5 minute expiry), not a proxy through the API — keeps large file bytes off the FastAPI process, consistent with the upload design.
- v1.3 indexes **filenames only** into the existing Postgres full-text search (`tsvector`/GIN). Extracting and indexing the actual text content of PDFs/DOCX/XLSX is real scope (new parsing dependencies, background job, failure handling) and is deferred — see Potential Future Features.
- Ritchie's access to documents is unchanged by this plan: it already can read anything the CRM API exposes for a company/deal it has context on, and the existing Gmail-attachment path (`put_object`, trusted server-side write) is unaffected since the bug is isolated to the presigned-POST path.

## Key Product Decisions — Profile Editing

- Company and founder/person profiles should be editable from their detail pages with normal form controls, not only through API tooling.
- Keep editing inline or in a focused edit dialog depending on the existing page pattern. The important requirement is a clear Save/Cancel flow, server-side validation errors surfaced inline, and cache invalidation so the detail page reflects saved data immediately.
- Do not introduce a separate "founder" table in v1.3. Founders are represented by the existing person/contact model unless a later data-model review proves that is too limiting.
- Preserve audit behavior for profile changes. Any update path used by the UI should continue to record who changed what and when.
- Keep relationship editing scoped. v1.3 should support editing the profile's own fields and existing association fields that already exist in the data model; more complex relationship management can wait if it threatens the sprint.

## Key Product Decisions — Outreach Tracking

- Add a dedicated Outreach view that answers: who have I reached out to, when, through what channel, about which company/deal/person, what was the last touch, and what follow-up is needed.
- Prefer building on existing `Interaction`/task/activity data instead of creating a parallel outreach log if the existing model can represent the workflow cleanly.
- The default view should be chronological and filterable by owner, company, person/founder, deal, channel, and follow-up status.
- Outreach tracking is about operational visibility first. Automated email/calendar ingestion can enrich it where already available, but v1.3 should still work with manual logging.

## Key Product Decisions — Outreach Candidates

- Add a first-class Outreach Candidates view/list builder for turning verification signals into a working company reach-out list.
- The default candidate criteria for v1.3:
  - RIT alumni founder status is `active` or `unclear`.
  - Operational status is `operational` or `unclear`.
  - Funding stage fits pre-seed through Series A.
  - Company is not archived, passed, already invested, or otherwise excluded by existing CRM status.
  - Company has not been contacted recently, based on outreach/interaction history.
- Hard exclusions should keep companies out of default Outreach Candidates even if they otherwise score well: already invested, passed/inactive, outside the stage threshold, high-confidence not operational, high-confidence no active RIT alumni founder, archived, duplicate/merged record, or inside the recent outreach cooldown window.
- `unclear` alumni-founder or operational verification states should remain eligible by default, but with visible warnings and score-confidence penalties.
- The default outreach cooldown is 30 days from the last meaningful outbound touch: logged CRM outreach, Bcc-to-Ritchie email, or LinkedIn message memory. Passive enrichment does not count. If a follow-up task is due, the cooldown is overridden and the candidate should appear as `follow_up_needed` rather than being excluded.
- Candidate lists should be saveable so a user can return to the same working list rather than rebuilding filters every session.
- Candidate lists should be shared team queues by default, with optional per-item owner assignment, status tracking, and direct outreach logging from the list.
- Candidate lists should track the last activity actor for each company/person, whether that activity came from Ritchie identifying who sent a message or from a user/agent actively editing CRM state.
- Keep relationship/workflow activity separate from passive enrichment. "Last activity" means messages, outreach, task completion, profile edits, or status changes; Ritchie rescoring, LinkedIn checks, alumni verification, and operational verification should appear as "last verified/scored/enriched" metadata instead.
- Candidate statuses stay lightweight and pre-pipeline until a company becomes `review_needed`. At that point, the company `relationship_status` should become `review_needed` and the existing triage flow takes over: start investment review, monitor/nurture, or pass/inactivate.
- Candidate rows should have context-sensitive primary actions: `Log outreach` for `ready_to_contact`, `Add follow-up` for `contacted`, `Mark review needed` for `meeting_scheduled` or strong positive replies, and profile open as a secondary action.
- Ritchie may automatically move a candidate to `meeting_scheduled` when message evidence is concrete, such as a booked meeting, accepted scheduling link, or explicit agreed meeting time. Ritchie may automatically move a candidate to `review_needed` only when there is a stronger investment-review signal, such as fundraising interest, request to send materials, interest in discussing investment, or a completed intro meeting note.
- Any automatic status movement by Ritchie must record an evidence summary and source reference so the user can understand why the state changed.
- Candidate ranking should prioritize higher verification confidence, fresher evidence, warmer relationship context where available, companies with no recent outreach, higher screening-rubric score, and stronger investment-thesis alignment.
- Each candidate should receive an overall Outreach Candidate Score based on an initial v1.3 rubric that combines the signals discussed in this plan. The rubric is expected to be refined after real use.
- This feature should not become a generic marketing campaign system in v1.3. It is a focused workflow for building and working the current RIT alumni founder company list.

## Key Product Decisions — Outreach Candidate Score

- Add a single score for each outreach candidate so the list can be sorted and triaged quickly.
- The initial v1.3 score should combine:
  - RIT alumni founder status and confidence.
  - Operational status and confidence.
  - Funding stage fit for pre-seed through Series A.
  - 1829 screening rubric score.
  - 1829 investment thesis alignment.
  - Prior relationship warmth from LinkedIn memory, Bcc email memory, CRM interactions, and known relationship paths.
  - Recency of prior outreach, with recently contacted companies deprioritized unless follow-up is due.
  - Evidence freshness and missing-evidence penalties.
- The score must be explainable. Candidate rows should show the total score plus a compact "Why this company" summary and score breakdown.
- Do not overfit the first rubric. Store weights/criteria in a way that can be changed later without rewriting the candidate-list feature.
- Users can manually override candidate status/priority even when the score ranks a company highly or poorly.

## Key Product Decisions — Thesis/Rubric-Aware Candidate Scoring

- Add rubric/thesis scoring as a candidate ranking signal. A company that scores slightly higher against the 1829 screening rubric and aligns better with the 1829 investment thesis should take precedence over an otherwise similar candidate.
- Use `reference_files/"1829 Ventures Screening Rubric.pdf"` as the scoring source of truth for rubric criteria and `reference_files/"1829 Ventures Investment Thesis v2.7.docx"` as the source of truth for thesis goals.
- Scores must be explainable. Candidate rows should show the total score, major positive/negative factors, and a concise "why this fits 1829" note.
- Scoring should be based on existing CRM fields, Dealroom enrichment, documents, notes, and Ritchie-readable public/company context where allowed. Do not require users to manually fill a long scoring form before seeing a ranked list.
- Missing information should reduce confidence rather than silently forcing a low score. Ritchie should identify what evidence is missing when it cannot score confidently.
- The ranking should preserve the outreach workflow: fit score influences order, but users can still filter and manually override list priority/status.

## Key Product Decisions — LinkedIn Message Memory

- Add a read-only LinkedIn message memory workflow that helps the user avoid forgetting companies or people they have already interacted with.
- The workflow should ingest or connect to LinkedIn messages in read-only mode only. v1.3 should not send LinkedIn messages, mark messages read/unread, delete messages, or mutate LinkedIn state.
- Ritchie/kernelbot should comb through messages to identify people, companies, conversation dates, topics, follow-up hints, and likely CRM matches.
- Organize the output as a durable "interaction memory" view: company/person, last LinkedIn touch, summary, auto-created follow-up task when warranted, confidence of CRM match, and source-message reference.
- Link memory items to existing CRM company/person records where confidence is high; queue ambiguous matches for review without blocking the user from seeing them.
- Surface LinkedIn memory in company/person profiles and Outreach Candidates so a company is not treated as cold if the user has already interacted with someone relevant.
- Ritchie should automatically create follow-up tasks from LinkedIn messages when the conversation implies a clear next step, such as "send me the deck," "circle back next month," or "follow up after fundraising." Users can dismiss or edit those tasks after creation.
- Do not over-optimize low-value task filtering in v1.3. Task quality thresholds can be tuned later based on the user's preferences after seeing real Ritchie-created tasks.
- Prevent obvious duplicates: before creating a LinkedIn-derived follow-up task, Ritchie should check for an existing open task for the same person/company/topic, merge repeated reminders into the existing task where possible, and link the memory item to that existing task instead of creating another one.
- Ritchie-created tasks must be visually distinguishable from human-created tasks with a tiger logo or tiger-style badge in the top-right of the task row/card/detail surface, plus normal actor/audit attribution.
- Respect privacy and access boundaries: store only the minimum message excerpts/summaries needed for recall, preserve source references, and make the read-only provenance visible.

## Key Product Decisions — Email and Calendar Memory Boundaries

- Ritchie already has the capability to listen to emails when explicitly added in Bcc. v1.3 should use that existing explicit-copy workflow for email memory and should not request broad Gmail or inbox visibility.
- Email-derived memory/task creation should only come from messages Ritchie was intentionally included on, not from scanning the user's mailbox.
- Calendar visibility is not in v1.3 scope. It may become a later relationship-memory input, but Ritchie should not view calendars until that permission is explicitly added.
- The product boundary should be visible in docs/settings: LinkedIn message memory is read-only if configured, email memory is Bcc-only, and calendar access is not enabled.

## Key Product Decisions — RIT Alumni Founder Verification

- Add an outreach-list-building capability for the current target segment: companies that have at least one RIT alumni founder, are operational, and fit the pre-seed to Series A threshold.
- Dealroom is treated as reliable for identifying founder universities, but not for whether that founder is still with the company.
- Ritchie/kernelbot should use the Dealroom-provided LinkedIn URL for the RIT alumni founder and attempt to determine whether the founder still appears active at the company, looking for current-role evidence such as a LinkedIn experience date range ending in "present".
- Do not require human confirmation before using the verification result. Ritchie writes its best confidence-scored assessment directly to the CRM, with evidence and uncertainty visible.
- The company profile should show the result in the top-right profile area:
  - Checkbox/check icon: high confidence the RIT alumni founder is still active.
  - Warning icon: unclear or medium confidence.
  - X icon: high confidence the RIT alumni founder is no longer active or no active RIT alumni founder is found.
- Verification must be explainable: users can see the founder name, evidence URL, evidence note, confidence, status, verifier, and timestamp.
- This is not a generic alumni graph in v1.3. The first workflow is specifically "find reachable RIT alumni founder companies for pre-seed to Series A outreach."

## Key Product Decisions — Operational Status Verification

- Add a second Ritchie/kernelbot verification workflow for whether a company appears operational, because Dealroom's active/inactive flag is not reliable enough for outreach list building.
- Operational status should be assessed from multiple lightweight public signals where available:
  - Company website is live and not parked/dead.
  - Company or founder LinkedIn shows recent/current activity.
  - Founder or executive profiles still reference the company as current.
  - No obvious shutdown, acquisition, closed, dead-domain, or abandoned-social signals are found.
- Ritchie writes its best confidence-scored assessment directly to the CRM without requiring human confirmation.
- The company profile should show operational evidence near the company status area or in the same top-right profile badge cluster as the alumni-founder badge.
- Operational verification must be explainable: users can see the status, confidence, evidence URLs, evidence note, verifier, and timestamp.
- Outreach candidate views should default to verified/likely operational companies, while still allowing unclear companies to remain visible via filters.

## Key Product Decisions — MCP + Ritchie/kernelbot

- The MCP server is the integration boundary for agent access. Ritchie/kernelbot should use MCP tools instead of reaching directly into database tables or private backend internals.
- MCP updates are continuous work in this mini-sprint: whenever backend/frontend behavior changes, update MCP tool schemas, docs, and tests in the same change set.
- MCP tools should expose the product workflows Ritchie needs: read/search companies and people, update permitted profile fields, list/create/archive documents through CRM APIs, inspect outreach history, log outreach/follow-up actions, create/update outreach candidate lists, run/update thesis/rubric scoring, read and summarize LinkedIn message memory, run/update RIT alumni founder verification, and run/update operational-status verification.
- Ritchie must inherit the CRM permission model. If the current user or agent role cannot perform an action in the API, the MCP tool should not bypass that restriction.
- Prefer narrow, workflow-oriented MCP tools over overly broad generic mutation tools. This keeps permission checks, audit records, and future UI behavior aligned.

## Data Model — File Storage

No new tables. Two additions to `backend/app/models/document.py` / the storage layer:

- `Document.status` (new column, `String(16)`, default `"pending"`): `pending` (row created, upload not yet confirmed) → `confirmed` (verified in storage) → `rejected` (failed validation, object deleted). Only `confirmed` documents are returned by default from `GET /documents` (mirrors how `include_archived` already filters). Migration must backfill existing metadata, external-link, dealroom, email, and trusted-server-write documents to `confirmed` so v1/v1.2 data does not disappear. New external-link documents and Gmail/trusted `put_object` documents should also be created as `confirmed`, not `pending`.
- `PresignedUpload` dataclass (`app/integrations/storage.py`) gains a `fields: dict[str, str]` attribute so `generate_presigned_post`'s required form fields are no longer discarded. This is the core bug fix.
- `DocumentStorage` protocol gains these methods:
  - `create_presigned_download(*, storage_key: str, filename: str, expires_in: int = 300) -> str` — presigned GET URL, sets `ResponseContentDisposition` so the browser downloads with the original filename rather than the UUID-based storage key.
  - `head_object(*, storage_key: str) -> ObjectStat | None` — returns storage metadata such as real `size_bytes`, or `None` if the object doesn't exist.
  - `read_object_prefix(*, storage_key: str, byte_count: int = 4096) -> bytes` — ranged object read used for magic-byte sniffing in the confirm step.
  - `delete_object(*, storage_key: str) -> None` — used by the confirm step on rejection, and reserved for a future purge job.

## Data Model — Profile Editing

No new profile tables in v1.3 unless implementation discovers a missing required field that cannot be represented today.

- Company profile editing uses the existing company model and update route.
- Founder/person profile editing uses the existing person/contact model and update route.
- Any new optional profile fields must be added deliberately with migrations, schema updates, generated frontend types, audit coverage, and MCP schema updates.

## Data Model — Outreach Tracking

Prefer no new table if the existing interaction/task models can answer the outreach questions.

- If existing interactions already capture channel, timestamp, participants, company/deal/person links, notes, and owner, build the Outreach view as a query/view over interactions plus follow-up tasks.
- If the existing model is insufficient, add the smallest possible outreach-specific field(s), not a parallel CRM activity system.
- Outreach records must be attributable to a user/agent and linkable to company, person/founder, and optionally deal.

## Data Model — Outreach Candidates

Add lightweight persistence for saved candidate lists if existing saved-search/list infrastructure does not already exist.

- `OutreachCandidateList`:
  - `id`, `name`, `description`.
  - `created_by`, `created_at`, `updated_at`.
  - `default_filters` JSONB for the criteria used to build the list.
  - optional `owner_id` for the person accountable for the shared list.
  - `status`: `active`, `completed`, `archived`.
- `OutreachCandidateListItem`:
  - `id`, `list_id`, `company_id`.
  - optional `person_id` for the primary founder/contact to reach out to.
  - optional `assigned_to`.
  - `candidate_status`: `new`, `ready_to_contact`, `contacted`, `follow_up_needed`, `meeting_scheduled`, `review_needed`, `deferred`, `not_relevant`.
  - `rank_score` and `rank_reasons` JSONB so the list can explain why a company is near the top.
  - `outreach_candidate_score`, `outreach_candidate_score_breakdown`, and `why_this_company` for the combined v1.3 candidate rubric.
  - optional `rubric_score`, `thesis_alignment_score`, `score_confidence`, and `score_reasons` JSONB for fit-based ordering.
  - `last_outreach_at`, `last_outreach_interaction_id`.
  - optional `last_linkedin_touch_at` and `linkedin_memory_item_id` when prior LinkedIn context exists.
  - `last_activity_at`, `last_activity_by`, `last_activity_source`, and `last_activity_summary` so the queue shows who last touched the company/person through relationship/workflow activity and why.
  - Passive enrichment timestamps remain separate through the relevant verification/scoring fields, such as `rit_alumni_founder_verified_at`, `operational_status_verified_at`, and score `scored_at`.
  - optional `last_status_change_reason` and `last_status_change_source` for Ritchie/user status moves.
  - `created_at`, `updated_at`.
- If the app already has a reusable saved-list or task assignment model, use that instead of adding new tables, but preserve the same behavioral surface.
- List item status changes and assignment changes should be audited.
- When `candidate_status` becomes `review_needed`, update the linked company `relationship_status` to `review_needed` and create/use the existing triage task flow rather than creating a parallel investment pipeline.

## Data Model — Outreach Candidate Score

Persist the combined candidate score and the rubric version used to compute it.

- Candidate list items or a related score snapshot should include:
  - `outreach_candidate_score`: numeric score such as 0-100.
  - `outreach_candidate_score_breakdown` JSONB: component scores, weights, and evidence references.
  - `outreach_candidate_score_version`: rubric/weight version.
  - `why_this_company`: compact explanation generated by Ritchie.
  - `scored_at`, `scored_by`.
- Score snapshots should remain explainable after rubric changes. Refreshing a list can recompute scores with the latest version, but old score provenance should not be lost silently.

## Data Model — Thesis/Rubric-Aware Candidate Scoring

Add persistence for explainable fit scoring if no existing scoring model can represent it cleanly.

- `CompanyFitScore` or equivalent company-level score snapshot:
  - `company_id`.
  - `rubric_score`: numeric score derived from the screening rubric.
  - `thesis_alignment_score`: numeric score derived from the investment thesis.
  - `overall_fit_score`: combined value used for candidate ranking.
  - `score_confidence`: `high`, `medium`, `low`, or numeric equivalent.
  - `score_reasons` JSONB: positive/negative factors and evidence references.
  - `missing_evidence` JSONB: fields or documents Ritchie needs to score more confidently.
  - `rubric_source_version` and `thesis_source_version` or file hash so score provenance is clear when source docs change.
  - `scored_at`, `scored_by`.
- Score updates should be auditable and should not overwrite user-entered investment judgment without preserving history.
- Candidate-list snapshots should copy the score/rank reasons used at list creation or refresh so old lists remain explainable.

## Data Model — LinkedIn Message Memory

Add read-only memory records rather than treating LinkedIn messages as editable CRM interactions.

- `LinkedInMessageMemoryItem` or equivalent:
  - `id`.
  - `source_message_id` or stable source reference if available.
  - `person_name`, `company_name`, optional `linkedin_profile_url`.
  - optional `person_id`, `company_id` when matched to CRM records.
  - `conversation_started_at`, `last_message_at`.
  - `summary`: concise recall summary.
  - `follow_up_hint`: optional next-step reminder inferred by Ritchie.
  - optional `created_task_id` when Ritchie auto-creates a follow-up task from the message memory.
  - `match_confidence`: confidence for the CRM person/company match.
  - `source_excerpt`: minimal excerpt only when needed for recall/provenance.
  - `ingested_at`, `ingested_by`.
- Store raw LinkedIn exports/messages only if needed for reprocessing and only in a clearly marked read-only/import table or object-storage location.
- Preserve enough source reference to let the user find the original LinkedIn conversation manually.

## Data Model — Email and Calendar Memory Boundaries

- No new broad Gmail/inbox sync tables in v1.3.
- Existing email records created through the Bcc-to-Ritchie workflow can continue to link to companies, people, interactions, and tasks.
- If email-derived tasks are added, they must preserve the source as `email_bcc_ritchie` or equivalent so users can distinguish explicit-copy email memory from other sources.
- No calendar event storage/sync model is added in v1.3.

## Data Model — RIT Alumni Founder Verification

Add the smallest persistence layer needed to make Ritchie's assessment visible, filterable, and auditable.

- Company-level fields or a one-row-per-company verification table should capture the current rollup:
  - `rit_alumni_founder_status`: enum/string such as `active`, `unclear`, `inactive`, `not_found`, `unverified`.
  - `rit_alumni_founder_confidence`: numeric score or enum such as `high`, `medium`, `low`.
  - `rit_alumni_founder_verified_at`: timestamp of the latest assessment.
  - `rit_alumni_founder_verified_by`: user/agent actor, usually Ritchie/kernelbot.
  - `rit_alumni_founder_evidence_url`: Dealroom-provided LinkedIn URL or other source URL used for the assessment.
  - `rit_alumni_founder_evidence_note`: short explanation, for example "LinkedIn experience lists Founder at Acme, 2021-present."
  - `rit_alumni_founder_person_id`: optional link to the person/founder record when the founder exists in CRM data.
- If multiple RIT alumni founders exist, store the highest-confidence active founder as the company rollup and preserve enough evidence to understand which founder drove the badge.
- Verification updates must create audit records with actor identity and previous/new status.
- The outreach list must be able to filter by this verification status and confidence without re-running LinkedIn checks at query time.

## Data Model — Operational Status Verification

Add persistence for CRM-side operational status separate from the imported Dealroom active/inactive value.

- Company-level fields or a one-row-per-company verification table should capture the current rollup:
  - `operational_status`: enum/string such as `operational`, `unclear`, `not_operational`, `unverified`.
  - `operational_status_confidence`: numeric score or enum such as `high`, `medium`, `low`.
  - `operational_status_verified_at`: timestamp of the latest assessment.
  - `operational_status_verified_by`: user/agent actor, usually Ritchie/kernelbot.
  - `operational_status_evidence_urls`: list of source URLs checked, such as company website, LinkedIn, news, or founder profile URLs.
  - `operational_status_evidence_note`: short explanation, for example "Website live, LinkedIn company page posted in May 2026, founder still lists company as current."
- Keep imported Dealroom status available for comparison, but do not overwrite it with Ritchie's assessment.
- Verification updates must create audit records with actor identity and previous/new status.
- Outreach candidate queries must be able to filter by operational status and confidence without re-running public-signal checks at query time.

## Data Model — MCP + Ritchie/kernelbot

No product data tables are required just for MCP access in v1.3.

- MCP tool definitions, schemas, and tests must track the CRM API contracts.
- Ritchie/kernelbot actions should create the same audit trail as user-triggered API actions, with actor identity clearly represented as the agent where appropriate.

## API Surface — File Storage

Extends the existing `/documents` router (`backend/app/api/routes/documents.py`):

- `POST /documents/presigned-upload` (existing route, fixed): `PresignedUploadResponse` now also returns `fields: dict[str, str]` alongside `upload_url` and `storage_key`, so the frontend can build a correct multipart form POST. The generated policy should include allowed content type when known and a `content-length-range` condition using `S3_MAX_UPLOAD_MB`.
- `POST /documents/{document_id}/confirm` (new): frontend calls this after the browser-to-MinIO upload completes. Backend calls `head_object`, validates size against `S3_MAX_UPLOAD_MB` and content type against the allowlist, sets `status="confirmed"` with the verified `size_bytes`/`content_type` on success, or `status="rejected"` + `delete_object` + a 422 response on failure.
- `GET /documents/{document_id}/download` (new): returns `{ "download_url": str, "expires_in": int }` — a presigned GET URL. Only `confirmed`, non-archived documents are downloadable (404 otherwise).
- Existing routes (`list`, `get`, `archive`) unchanged in shape; `list_documents` gains an implicit filter to `status="confirmed"` unless the caller explicitly wants pending/rejected rows (admin/debug use only, not exposed in the frontend).
- `PATCH /documents/{document_id}` should not let normal clients mutate server-verified fields after confirmation (`storage_key`, `status`, verified `content_type`, verified `size_bytes`). Filename and associations can remain editable if the current API already permits them and audit records are preserved.

## API Surface — Profile Editing

- Confirm existing company update endpoints support all fields needed by the Company Detail edit form; add schema fields only where the model already supports them or where the sprint explicitly adds them.
- Confirm existing person/founder update endpoints support all fields needed by the founder profile edit form.
- API validation should distinguish required fields, nullable optional fields, and unsupported relationship changes clearly so the frontend can show useful errors.

## API Surface — Outreach Tracking

- Add or refine endpoints that return an Outreach timeline/list with filters for owner, company, person/founder, deal, channel, date range, and follow-up state.
- Support manual outreach logging if existing interaction creation does not already cover the workflow.
- Support creating a follow-up task from an outreach record if this is already close to the task model; otherwise defer the shortcut and keep the view read/log focused.

## API Surface — Outreach Candidates

- Add endpoints for candidate-list workflows:
  - Create a candidate list from filters.
  - List saved candidate lists.
  - Get a candidate list with ranked company items.
  - Refresh/recompute a list from its saved filters.
  - Update item assignment/status.
  - Log outreach from a candidate item, linking the resulting interaction/outreach record back to the list item.
- Candidate item status updates to `review_needed` should call the existing pipeline service behavior for review-needed triage setup, including company `relationship_status=review_needed` and the review-needed task.
- Ritchie-driven candidate status updates are allowed for:
  - `meeting_scheduled` when concrete meeting evidence exists.
  - `review_needed` when strong investment-review evidence exists.
- Ritchie-driven status updates must include evidence summary, source reference, actor identity, and previous/new status in the audit path.
- Candidate-list creation defaults to the v1.3 RIT alumni founder target segment but allows users to adjust filters before saving.
- Candidate-list creation should apply hard exclusions by default and expose why excluded companies were omitted when a user inspects list generation results.
- Candidate-list creation should apply the 30-day outreach cooldown by default, but due follow-up tasks override the cooldown and keep the candidate visible.
- Candidate-list item responses should include enough rollup data to work quickly: company name, primary founder/contact, funding stage, alumni-founder status/confidence, operational status/confidence, rubric score, thesis alignment score, LinkedIn prior-touch context, last outreach, assigned owner, rank reasons, and next action.
- Candidate-list item responses should include last activity actor/source/summary so users can see who most recently touched the company/person through relationship/workflow activity. Passive enrichment timestamps should be exposed separately as verification/scoring metadata.
- Candidate-list queries should not re-run Ritchie verification synchronously. Missing or stale verification should be visible as a warning state and can trigger a separate refresh/enrichment workflow.
- Candidate-list item responses should include a recommended `primary_action` derived from candidate status and recent activity so the frontend can render the fastest next action consistently.

## API Surface — Outreach Candidate Score

- Candidate-list item responses should include `outreach_candidate_score`, score breakdown, score version, and `why_this_company`.
- Candidate-list create/refresh should compute scores using the current v1.3 rubric.
- Add sort/filter support for candidate score ranges and stale score version.
- Score computation should tolerate missing signals by reducing confidence or applying missing-evidence penalties rather than failing the list build.

## API Surface — Thesis/Rubric-Aware Candidate Scoring

- Add backend/service capability for computing or refreshing company fit scores from the screening rubric and investment thesis.
- Expose fit-score fields on company detail and candidate-list responses: rubric score, thesis alignment score, overall fit score, confidence, score reasons, missing evidence, scored-at timestamp, and scorer.
- Add filters/sorts for candidate lists:
  - minimum rubric score.
  - minimum thesis alignment score.
  - score confidence.
  - stale score date.
- Source-doc changes should make old scores stale via file hash/version comparison.

## API Surface — LinkedIn Message Memory

- Add read-only import/sync endpoints or service boundaries for LinkedIn message data. The API should accept an export/upload or connector-backed read result, but it must not expose any write action against LinkedIn.
- Add endpoints for listing memory items, matching/unmatching a memory item to CRM company/person records, marking a memory item as reviewed if review state is needed, and surfacing the task created from a memory item.
- Ritchie may auto-create CRM follow-up tasks from LinkedIn message memory when a clear next action exists. These are CRM task writes, not LinkedIn writes, and must use the same task/audit path as other Ritchie-created actions.
- The task creation service should dedupe against existing open tasks by person/company/topic before creating a new LinkedIn-derived task. If a likely duplicate exists, update/link the existing task rather than creating another task.
- Expose LinkedIn memory rollups on company/person detail responses and candidate-list item responses: last LinkedIn touch, summary, follow-up hint or created task, match confidence, and source reference.
- Add filters for "has prior LinkedIn interaction", "last LinkedIn touch before/after", "unmatched LinkedIn memory", and "follow-up hinted".

## API Surface — Email and Calendar Memory Boundaries

- Keep email APIs limited to the existing Bcc-to-Ritchie ingestion path and CRM records derived from those explicitly copied emails.
- Do not add Gmail OAuth, inbox search, mailbox sync, or all-mail read endpoints in v1.3.
- Do not add calendar read/sync endpoints in v1.3.
- Any relationship-memory API response that includes email context should label it as Bcc-derived so provenance is unambiguous.

## API Surface — RIT Alumni Founder Verification

- Add filters to the company list/search endpoint for outreach list building:
  - has RIT alumni founder verification status.
  - operational status.
  - funding stage/range covering pre-seed through Series A.
  - confidence threshold.
  - last verified before/after date so stale assessments can be refreshed.
- Add a backend endpoint or service boundary for updating alumni-founder verification results. It should require the same permissions as other agent-written profile enrichment and should write audit records.
- Expose the current verification rollup on company detail responses so the profile page can render the badge without an additional request.
- If a batch verification workflow is added, it should queue/check companies from the filtered outreach candidate set and update verification fields incrementally.

## API Surface — Operational Status Verification

- Add filters to the company list/search endpoint for:
  - operational status (`operational`, `unclear`, `not_operational`, `unverified`).
  - operational confidence threshold.
  - last operational verification before/after date so stale assessments can be refreshed.
  - mismatch between Dealroom status and CRM/Ritchie operational assessment.
- Add a backend endpoint or service boundary for updating operational verification results. It should require the same permissions as other agent-written profile enrichment and should write audit records.
- Expose the current operational verification rollup on company detail responses so the profile page and outreach candidate views can render it without an additional request.
- If a batch verification workflow is added, it should prioritize companies that otherwise match the RIT alumni founder and funding-stage criteria but have missing/stale operational verification.

## API Surface — MCP + Ritchie/kernelbot

- Update MCP tools after each relevant API change, especially profile update, document upload/list/download/archive, outreach list/log, and search/read endpoints.
- MCP tools must call CRM APIs or shared service boundaries so permission checks and audit behavior stay consistent.
- Add MCP-facing affordances for Ritchie/kernelbot:
  - Read/search companies, people/founders, deals, documents, and outreach history.
  - Update permitted company/person fields.
  - Attach/list/archive documents through the document workflow.
  - Log outreach and follow-up actions.
  - Create, refresh, assign, and work outreach candidate lists.
  - Score companies against the screening rubric and investment thesis and explain the scoring evidence.
  - Read/summarize LinkedIn message memory and link high-confidence memory items to CRM records without mutating LinkedIn.
  - Find RIT alumni-founder outreach candidates and update the alumni-founder verification assessment after checking the Dealroom-provided LinkedIn URL.
  - Update operational-status verification after checking company website, LinkedIn/company activity, founder activity, and shutdown/dead-domain signals.

## Frontend — File Storage

- `frontend/src/api/documents.ts` gains:
  - `useCreatePresignedUpload()` — `POST /documents/presigned-upload`.
  - `useConfirmDocument()` — `POST /documents/{id}/confirm`.
  - `useDownloadDocument()` — `GET /documents/{id}/download`, opens the returned URL in a new tab.
  - `useArchiveDocument()` — `POST /documents/{id}/archive`, matching the existing `useArchiveDeal`/`useArchiveTask` convention.
- New `frontend/src/components/document/DocumentUploadZone.tsx` — drag-and-drop dropzone plus a click-to-browse fallback, mirroring the modal conventions already established in this codebase (`TaskCreateDialog.tsx`, `CloseInvestmentDialog.tsx`: controlled inputs, `Field` label wrapper, inline error text, disabled-while-pending buttons). Upload sequence: request presigned upload → `FormData` POST directly to the browser-reachable MinIO URL with the returned `fields` + file → confirm → invalidate `["documents", ...]`. Client-side extension check gives instant feedback before the network round-trip; the server-side check in the confirm step remains the actual source of truth.
- `frontend/src/pages/CompanyDetail.tsx`'s existing "Documents" card is replaced with a real `DocumentList` component: file-type icon (lucide-react: `FileText` for pdf/docx/md/txt, `FileSpreadsheet` for xlsx/csv, `FileImage` for images), filename, size (human-readable), uploaded-by/at, a Download button, and an Archive button (with the same `ConfirmDialog` pattern used elsewhere for destructive-ish actions). The upload zone renders above the list.
- Same `DocumentList`/`DocumentUploadZone` components are written to accept `companyId`, `personId`, or `dealId` props. The v1.3 UI must wire them into company and founder/person profiles; deal-level reuse can follow when the deal detail page needs it.

## Frontend — Profile Editing

- Company detail page gains an Edit action for the company profile. The edit surface should cover the fields users actually need to maintain day to day: company name, website/domain, description/notes, sector/tags, status/stage fields already present in the data model, and any existing ownership/relationship fields the API supports.
- Founder/person profile page gains an Edit action for the founder/person profile. The edit surface should cover name, title/role, email, phone, LinkedIn/social URL, notes, and company association fields already supported by the model.
- Use existing API hooks and generated OpenAPI types where possible; add missing hooks next to the existing company/person API modules.
- Successful saves invalidate the relevant profile queries and update the displayed profile without a full page refresh.
- Failed saves surface server validation errors next to the relevant field when possible and show a concise form-level error otherwise.

## Frontend — Outreach Tracking

- Add a dedicated Outreach route/page in the main app navigation.
- The default view is a dense, scannable table or timeline of outreach records with columns for person/founder, company, deal if present, last contact date, channel, owner, summary, and follow-up status.
- Filters: owner, company, person/founder, deal, channel, date range, and follow-up status.
- Provide a manual "Log outreach" action if the existing interaction creation UI does not already make this workflow obvious.
- Clicking an outreach row should navigate to the relevant person/company/deal context or open a compact detail view, depending on existing navigation patterns.

## Frontend — Outreach Candidates

- Add an Outreach Candidates route or tab adjacent to the Outreach view.
- Default view loads the current target segment: RIT alumni founder active/unclear, operational/unclear, pre-seed through Series A, not recently contacted, and not excluded by company status.
- Default candidate generation excludes already invested, passed/inactive, outside-stage, high-confidence not operational, high-confidence no active RIT alumni founder, archived, duplicate/merged, and recently contacted companies.
- Recently contacted means a meaningful outbound touch in the last 30 days. Due follow-up tasks override the cooldown and keep the row visible as `follow_up_needed`.
- The page should support:
  - Filter controls for alumni-founder status/confidence, operational status/confidence, funding stage, last outreach date, owner, and candidate status.
  - Save list / refresh list actions.
  - Dense table rows with company, primary founder/contact, Outreach Candidate Score, "Why this company" summary, funding stage, alumni-founder badge, operational badge, rubric score, thesis alignment score, LinkedIn prior-touch indicator, last outreach, assigned owner, candidate status, rank reasons, and next action.
  - Optional owner assignment and candidate status updates inline.
  - Last activity actor/source/summary inline so the team can see who last sent a relevant message, logged outreach, completed a task, edited the person/company, or changed workflow status.
  - Passive enrichment timestamps, such as last verified/scored/enriched, appear inside badges, score details, or metadata tooltips rather than in the last-activity column.
  - Direct "Log outreach" action from a candidate row.
  - Row navigation to company/person context.
- The primary row action should be context-sensitive:
  - `ready_to_contact`: `Log outreach`.
  - `contacted`: `Add follow-up`.
  - `follow_up_needed`: complete/log the follow-up.
  - `meeting_scheduled`: `Mark review needed`.
  - strong positive reply signal: `Mark review needed`.
  - profile/company open remains available as a secondary action.
- Moving a candidate to `review_needed` should make the handoff explicit in the UI: the row should show that the company has entered the existing review-needed triage flow, not a separate candidate-only stage.
- When Ritchie automatically moves a candidate status, the row should show a concise evidence note and Ritchie attribution near the status so the change does not look like a silent human edit.
- Saved lists should be accessible from the same page so users can resume a working list.
- Keep the UI operational and scannable; this is a work queue, not a marketing dashboard.

## Frontend — Outreach Candidate Score

- Outreach Candidates table shows the combined score prominently enough to sort/triage quickly, but not so large that it crowds operational fields.
- Each row includes a compact "Why this company" explanation generated by Ritchie.
- Score breakdown is available in a tooltip/popover or row detail, showing component contributions and missing evidence.
- Filters include score range, stale score version, and missing-evidence warnings.

## Frontend — Thesis/Rubric-Aware Candidate Scoring

- Company detail page shows a compact fit-score section with rubric score, thesis alignment score, confidence, scored-at timestamp, and top score reasons.
- Outreach Candidates table includes fit-score columns and uses score/rank reasons to explain why a company appears near the top.
- Candidate filters include minimum rubric score, minimum thesis alignment score, score confidence, and stale score.
- Missing evidence should appear as a warning/tooltip so users know what data would improve the score.

## Frontend — LinkedIn Message Memory

- Add a LinkedIn Memory route or tab that lists companies/people the user has interacted with via LinkedIn messages.
- The default view should be organized for recall and follow-up: company/person, CRM match, last message date, summary, follow-up hint or auto-created task, match confidence, and source reference.
- Company and person profile pages show a "LinkedIn memory" section or badge when prior LinkedIn interaction exists.
- Outreach Candidates table shows a prior-touch indicator and last LinkedIn touch date so warm contacts are not forgotten.
- Provide review/match controls for ambiguous memory items, but keep LinkedIn access read-only.
- Ritchie-created follow-up tasks display a tiger logo or tiger-style badge in the top-right of task rows/cards/details so the user can instantly tell the task came from Ritchie. The task remains editable and dismissible like any other CRM task.

## Frontend — Email and Calendar Memory Boundaries

- Relationship-memory surfaces may show email context only when it came from the explicit Bcc-to-Ritchie workflow.
- Settings/docs UI, if touched, should make the boundary clear: Ritchie does not have broad Gmail/inbox access and does not have calendar access in v1.3.
- Calendar context should not appear in v1.3 relationship-memory UI except as a future/disabled capability if such a settings surface already exists.

## Frontend — RIT Alumni Founder Verification

- Company detail page shows a top-right verification badge for "RIT alumni founder still active":
  - Check icon for high-confidence active.
  - Warning icon for unclear/medium-confidence or stale verification.
  - X icon for high-confidence inactive/not found.
- Badge tooltip/popover shows founder name, status, confidence, evidence URL, evidence note, verifier, and verified-at timestamp.
- Company list/search and the Outreach candidate builder can filter for:
  - RIT alumni founder active/unclear/inactive/unverified.
  - operational companies.
  - funding stage from pre-seed through Series A.
  - confidence threshold.
- Add an "RIT alumni founder candidates" saved filter or first-class view if it fits the existing navigation better than burying the workflow in generic company filters.
- Do not block users behind a confirmation step. The UI should make confidence visible rather than requiring manual approval.

## Frontend — Operational Status Verification

- Company detail page shows an operational-status badge near the company status or in the same badge cluster as alumni-founder verification:
  - Check icon for high-confidence operational.
  - Warning icon for unclear/medium-confidence or stale verification.
  - X icon for high-confidence not operational.
- Badge tooltip/popover shows status, confidence, evidence URLs, evidence note, verifier, verified-at timestamp, and imported Dealroom status for comparison.
- Company list/search and the Outreach candidate builder can filter for:
  - operational/unclear/not operational/unverified.
  - confidence threshold.
  - stale verification.
  - Dealroom/CRM operational-status mismatch.
- Outreach candidate defaults should prefer operational companies, but leave unclear companies one filter away so potentially good candidates are not buried permanently.

## Frontend — MCP + Ritchie/kernelbot

- No broad agent UI is required for v1.3 unless an existing Ritchie surface already exists. The frontend requirement is mostly visibility: actions performed by Ritchie should appear in normal profile/document/outreach views with clear actor/audit attribution.
- If an MCP/server status surface exists, update it to reflect newly available tools and recent sync/update status. If it does not exist, keep this as backend/MCP test coverage rather than adding a new UI just for the sprint.

## Test Plan — File Storage

- Unit tests:
  - `MinioDocumentStorage.create_presigned_upload` returns `fields` (regression test for the bug fix — assert the returned dict is non-empty and includes a policy field).
  - Presigned upload policy includes a max-size `content-length-range` condition.
  - `head_object` correctly reports size, and `read_object_prefix` supports magic-byte sniffing independent of a spoofed extension.
  - Confirm-upload service logic: oversized file → `rejected` + object deleted; disallowed type → `rejected` + object deleted; valid file → `confirmed` with real size/content-type persisted.
  - Existing/external-link/Gmail/trusted-server-write documents are `confirmed` by default or via migration backfill.
  - Download endpoint 404s for `pending`/`rejected`/archived documents.
- Integration tests (against a real MinIO test bucket via the existing Docker Compose stack, or `moto`-mocked S3):
  - Full lifecycle: presigned-upload → direct upload to storage → confirm → download → archive.
  - Browser-direct upload uses a browser-reachable upload URL, not the Docker-internal `http://minio:9000` URL.
  - MinIO bucket CORS permits the frontend origin to perform the presigned POST and download flow.
  - Reject path: upload an executable renamed to `.pdf`, confirm it, assert `rejected` status and that the object no longer exists in the bucket.
- Acceptance scenario: upload a real `.pdf`, `.md`, `.xlsx`, `.csv`, and `.docx` from the company detail page, confirm each appears with the correct icon, download each and verify the bytes round-trip unchanged.
- Acceptance scenario: upload a document from a founder/person profile and verify it appears only in the expected person context plus any intentionally shared company context.

## Test Plan — Profile Editing

- Unit/service tests for company and person update paths that verify validation, audit records, and unchanged fields.
- Frontend tests for opening the edit form, changing representative fields, saving successfully, and showing validation errors.
- Acceptance scenario: edit a company profile and a founder/person profile from the UI, refresh the page, and verify persisted values.

## Test Plan — Outreach Tracking

- API tests for outreach list filters and manual outreach logging.
- Frontend tests for the Outreach page default rendering, filtering, and row navigation/detail behavior.
- Acceptance scenario: log outreach to a founder, associate it to a company, create or mark a follow-up state if supported, and verify the record appears in the Outreach view and relevant profile context.

## Test Plan — Outreach Candidates

- API tests for creating a candidate list from the default target-segment filters, retrieving ranked items, refreshing the list, updating assignment/status, and logging outreach from a candidate item.
- Exclusion tests proving hard-excluded companies do not enter the default candidate list, while `unclear` verification states remain eligible with warnings.
- Cooldown tests proving a 30-day meaningful-outbound touch excludes/deprioritizes a candidate, passive enrichment does not count, and due follow-up tasks override the cooldown.
- Ranking tests that prove higher verification confidence, fresher evidence, warm relationship signals, stronger rubric/thesis scores, prior LinkedIn context, and no recent outreach improve ordering.
- Frontend tests for default candidate list rendering, filter changes, saved list access, inline assignment/status updates, and log-outreach action.
- Tests for shared candidate queues with unassigned items, assigned items, and last activity actor/source rollups.
- Tests proving passive enrichment events do not overwrite relationship/workflow last activity.
- Tests for context-sensitive primary actions across candidate statuses.
- Tests for Ritchie auto-moving candidates to `meeting_scheduled` from concrete meeting evidence and to `review_needed` from stronger investment-review evidence, including audit/evidence records.
- Acceptance scenario: create a saved Outreach Candidates list for RIT alumni founder companies, assign three companies to an owner, log outreach for one, and verify the candidate item status plus Outreach view update correctly.
- Acceptance scenario: move a candidate to `review_needed`, verify the company relationship status becomes `review_needed`, the existing triage task is created, and the candidate does not create a parallel deal pipeline stage.
- Acceptance scenario: refresh a saved candidate list after Ritchie updates operational/alumni-founder verification and verify rank/status badges update without losing manual assignments.

## Test Plan — Outreach Candidate Score

- Scoring tests proving the initial rubric combines alumni-founder status, operational status, funding stage, rubric score, thesis alignment, relationship warmth, recent outreach, evidence freshness, and missing evidence.
- API tests proving candidate-list create/refresh returns score, score breakdown, score version, and "Why this company."
- Frontend tests for score display, score sorting/filtering, "Why this company" rendering, and score breakdown tooltip/popover.
- Acceptance scenario: generate a candidate list and verify the top-ranked company has a higher combined score with an explainable breakdown.

## Test Plan — Thesis/Rubric-Aware Candidate Scoring

- Source parsing tests proving the screening rubric PDF and investment thesis DOCX can be loaded, versioned/hashed, and converted into scoring criteria.
- Scoring tests for representative companies that verify rubric score, thesis alignment score, confidence, score reasons, and missing-evidence behavior.
- Candidate ranking tests proving a slightly higher rubric/thesis-aligned company takes precedence over an otherwise similar candidate.
- Frontend tests for fit-score display, score filters, stale score warnings, and missing-evidence tooltips.
- Acceptance scenario: score two eligible RIT alumni founder candidates and verify the higher rubric/thesis fit appears first with an explainable reason.

## Test Plan — LinkedIn Message Memory

- Import/sync tests using a small fixture of LinkedIn message data that prove read-only ingestion, person/company extraction, CRM matching, summaries, follow-up hints, auto-created tasks, and source references.
- Permission/safety tests proving no LinkedIn write/send/delete/mark-read operation exists in the API, MCP tools, or connector path.
- Task tests proving Ritchie-created LinkedIn follow-up tasks use the standard CRM task/audit path, dedupe against existing open tasks for the same person/company/topic, are dismissible/editable, and are visually marked as Ritchie-created.
- Matching tests for high-confidence matches, ambiguous matches, and unmatched people/companies.
- Frontend tests for LinkedIn Memory list, profile memory section/badge, candidate prior-touch indicator, tiger badge on Ritchie-created tasks, and ambiguous-match review controls.
- Acceptance scenario: ingest LinkedIn messages, identify a company/person already interacted with, auto-create a follow-up task from a clear next-step message, show the memory item in the LinkedIn Memory view, surface it on the company profile, mark the task with the tiger badge, and prioritize it in Outreach Candidates.

## Test Plan — Email and Calendar Memory Boundaries

- Permission/safety tests proving v1.3 does not add Gmail OAuth, broad inbox read, mailbox sync, or calendar read/sync capabilities.
- API tests proving email-derived memory/task records are limited to the existing Bcc-to-Ritchie ingestion path.
- Frontend tests, if settings/docs are touched, proving the UI labels email memory as Bcc-only and calendar access as not enabled.
- Acceptance scenario: an email with Ritchie in Bcc can create/update CRM context, while an email not copied to Ritchie remains invisible to the CRM.

## Test Plan — RIT Alumni Founder Verification

- Unit/API tests for persisting verification status, confidence, evidence URL, evidence note, verifier, timestamp, and audit records.
- Company list/search filter tests for operational status, funding stage pre-seed through Series A, alumni-founder status, confidence threshold, and stale verification date.
- MCP/tool tests for Ritchie finding candidate companies and updating verification results only through permitted CRM/MCP boundaries.
- Frontend tests for the company profile badge states: check, warning, and X; verify tooltip/popover content renders evidence and confidence.
- Acceptance scenario: Ritchie checks a Dealroom-provided LinkedIn URL for an RIT alumni founder, records a high-confidence active result, and the company profile shows the check icon plus evidence.
- Acceptance scenario: Ritchie records an unclear result and the company remains filterable with a warning state rather than being silently excluded.

## Test Plan — Operational Status Verification

- Unit/API tests for persisting operational status, confidence, evidence URLs, evidence note, verifier, timestamp, imported Dealroom comparison, and audit records.
- Company list/search filter tests for operational status, confidence threshold, stale verification date, and Dealroom/CRM mismatch.
- MCP/tool tests for Ritchie finding candidate companies and updating operational verification results only through permitted CRM/MCP boundaries.
- Frontend tests for company profile operational badge states: check, warning, and X; verify tooltip/popover content renders evidence, confidence, and Dealroom comparison.
- Acceptance scenario: Ritchie checks a company website and LinkedIn activity, records a high-confidence operational result, and the outreach candidate view includes the company by default.
- Acceptance scenario: Ritchie records a high-confidence not-operational result for a dead website/shutdown signal and the outreach candidate view excludes the company by default while keeping it searchable.

## Test Plan — MCP + Ritchie/kernelbot

- MCP schema/tool tests for each new or changed capability: profile read/update, document list/create/archive/download handoff, outreach list/log, and search/read.
- Permission tests proving MCP tools cannot perform actions the agent/user role is not allowed to perform.
- Audit tests proving Ritchie/kernelbot actions are recorded with the correct actor identity.
- Smoke scenario: through MCP, Ritchie reads a company, updates an allowed profile field, lists company documents, verifies RIT alumni founder activity, verifies operational status, logs outreach, and cannot perform a disallowed action.

## Build Sequence — File Storage

1. Backend: fix `PresignedUpload`/`create_presigned_post` field passthrough; add `Document.status` column + migration/backfill; add `head_object`/`read_object_prefix`/`create_presigned_download`/`delete_object` to the storage protocol and MinIO adapter; add the confirm and download routes; add the allowlist constants and `S3_MAX_UPLOAD_MB` setting.
2. Backend/config: add public/browser storage endpoint handling, presigned POST max-size policy, and MinIO bucket CORS setup in local Docker/init.
3. Backend: add `python-magic` for content-type sniffing (new dependency — requires `libmagic1` in the API/worker Docker image; update `backend/Dockerfile`).
4. Backend tests for the above.
5. Frontend: `documents.ts` mutation hooks, `DocumentUploadZone`, `DocumentList`, wire both into company and founder/person profile pages.
6. Manual smoke test: upload/download/archive one file of each allowed type end-to-end via the running app.

## Build Sequence — Profile Editing

1. Audit the current company/person schemas and detail pages to identify exactly which fields are already editable through the API.
2. Add or repair frontend API hooks for company/person updates.
3. Build company profile edit UI and wire cache invalidation.
4. Build founder/person profile edit UI and wire cache invalidation.
5. Add backend/frontend tests and manually edit one company plus one founder/person profile.

## Build Sequence — Outreach Tracking

1. Audit existing interactions/tasks to decide whether Outreach can be a query over existing data.
2. Add/refine backend query endpoints and manual log endpoint if needed.
3. Add frontend Outreach route, navigation entry, table/timeline, filters, and row actions.
4. Add tests and manually verify a logged outreach record appears in both the Outreach view and relevant profile context.

## Build Sequence — Outreach Candidates

1. Audit whether existing saved-search/list/task models can represent candidate lists, assignments, and statuses.
2. Add candidate-list persistence or reuse existing list/task infrastructure with migration, schemas, optional assignment, last-activity rollups, and audit handling.
3. Add candidate-list APIs for create/list/get/refresh/update-item/log-outreach, including Ritchie status automation and the `review_needed` handoff into the existing pipeline service.
4. Add the initial Outreach Candidate Score rubric and ranking logic based on verification confidence, evidence freshness, relationship warmth, funding stage fit, rubric score, thesis alignment, LinkedIn/Bcc prior-touch context, and recent outreach.
5. Add frontend Outreach Candidates route/tab, filters, saved list picker, dense table, inline optional assignment/status updates, last-activity actor display, and context-sensitive primary actions.
6. Add tests and manually create/work a saved RIT alumni founder candidate list end to end.

## Build Sequence — Outreach Candidate Score

1. Define the initial v1.3 scoring rubric and weights from the signals in this plan.
2. Add score computation with score versioning, breakdowns, missing-evidence handling, and "Why this company" generation.
3. Integrate score computation into candidate-list create/refresh.
4. Add frontend score display, sorting/filtering, explanation, and breakdown UI.
5. Add tests and manually review the top 10 ranked candidates for obvious scoring failures.

## Build Sequence — Thesis/Rubric-Aware Candidate Scoring

1. Build source-doc parsing/versioning for `reference_files/"1829 Ventures Screening Rubric.pdf"` and `reference_files/"1829 Ventures Investment Thesis v2.7.docx"`.
2. Define the scoring schema and add fit-score persistence, API schemas, and audit/provenance handling.
3. Add Ritchie scoring workflow that produces rubric score, thesis alignment score, confidence, score reasons, and missing evidence.
4. Add candidate ranking integration and frontend score display/filters.
5. Add tests and manually compare two similar candidates to verify the better thesis/rubric fit ranks first.

## Build Sequence — LinkedIn Message Memory

1. Decide the read-only source path for LinkedIn messages: export upload, connector, or local archive.
2. Add read-only ingestion/sync service, storage model, CRM matching logic, and source-reference handling.
3. Add API/MCP tools for listing memory items, summarizing interactions, linking high-confidence matches, auto-creating CRM follow-up tasks from clear next steps, deduping against existing open tasks for the same person/company/topic, and reviewing ambiguous matches without mutating LinkedIn.
4. Add LinkedIn Memory view plus profile/candidate-list rollups.
5. Add tiger-logo/tiger-style badge treatment for Ritchie-created tasks across task rows/cards/details.
6. Add tests and manually ingest a small LinkedIn message fixture to verify companies/people are remembered, follow-up tasks are created, and task origin is visually obvious.

## Build Sequence — Email and Calendar Memory Boundaries

1. Audit the existing Bcc-to-Ritchie email ingestion path and document which CRM records it can already create/update.
2. Ensure relationship-memory/candidate-list rollups can include Bcc-derived email context without adding broad Gmail/inbox permissions.
3. Add provenance labels for `email_bcc_ritchie` where email-derived context appears.
4. Add tests proving no broad Gmail or calendar access is introduced.

## Build Sequence — RIT Alumni Founder Verification

1. Audit company/person/Dealroom import fields for founder education, founder LinkedIn URL, operational status, and funding stage coverage.
2. Add verification persistence fields or table, migration/backfill defaults, API schemas, audit handling, and company list/search filters.
3. Add MCP/Ritchie workflow for selecting candidate companies, reading the Dealroom-provided LinkedIn URL, assessing current-company evidence, and writing status/confidence/evidence back to CRM.
4. Add frontend company profile badge, tooltip/popover, and company/outreach candidate filters.
5. Add tests and manually verify check/warning/X states on representative companies.

## Build Sequence — Operational Status Verification

1. Audit company/person/Dealroom import fields for website URL, LinkedIn URLs, imported Dealroom status, founder links, funding stage, and any existing last-activity signals.
2. Add operational verification persistence fields or table, migration/backfill defaults, API schemas, audit handling, and company list/search filters.
3. Add MCP/Ritchie workflow for selecting candidate companies, checking website/company activity/founder activity/shutdown signals, and writing status/confidence/evidence back to CRM.
4. Add frontend company profile badge, tooltip/popover, and outreach candidate filters.
5. Add tests and manually verify check/warning/X states on representative companies, including at least one Dealroom-active company that Ritchie marks not operational.

## Build Sequence — MCP + Ritchie/kernelbot

1. Update MCP server schemas/tools after the profile, document, and outreach API changes.
2. Add MCP tests for new tools and permission boundaries.
3. Integrate Ritchie/kernelbot through MCP tools only, using the existing agent identity and permission model, including alumni-founder and operational-status verification updates.
4. Run an end-to-end MCP smoke test against the local app.
5. Treat MCP updates as continuous work during the sprint: any API behavior change that affects agent access must include the corresponding MCP update before the work is considered complete.

## Assumptions — File Storage

- No AV/malware scanning engine (e.g. ClamAV) is introduced in v1.3. Magic-byte + extension allowlisting is the v1.3 defense; this is an internal-team tool behind RIT-Google-gated auth, not a public upload surface. Revisit if the threat model changes.
- `python-magic` requires the system `libmagic1` package — this is a new OS-level dependency for the API/worker containers, not just a Python package.
- Content-text extraction/indexing (PDF, DOCX, XLSX) and document versioning are both explicitly out of scope for this pass — see below.

## Assumptions — Profile Editing

- Founder means the existing person/contact record associated with a company unless the product later introduces a dedicated founder concept.
- v1.3 profile editing should prefer fields that already exist. New fields are acceptable only when clearly required for day-to-day use.

## Assumptions — Outreach Tracking

- Manual outreach logging is acceptable in v1.3 even if automated email/calendar capture is incomplete.
- The Outreach view should include Ritchie/kernelbot-created outreach entries if those actions are permitted and audited.

## Assumptions — Outreach Candidates

- The first candidate-list workflow is for the RIT alumni founder target segment, not every possible sourcing strategy.
- Hard exclusions protect list quality; warnings preserve uncertain opportunities.
- Saved candidate lists need to preserve manual assignment/status work even when verification data changes and the list is refreshed.
- Saved candidate lists are shared team queues by default; assignment is optional because some companies may be triaged before an owner is chosen.
- Last activity should prefer the most recent meaningful CRM edit, logged outreach, Bcc email, or LinkedIn memory touch with an identifiable sender/actor.
- Passive Ritchie enrichment should never make a company look recently contacted or actively worked. Verification/scoring/enrichment timestamps are separate metadata.
- "Recently contacted" should be based on the outreach/interaction model used elsewhere in v1.3.
- The default recent-outreach cooldown is 30 days and should be configurable later if real usage shows a different cadence.
- Outreach Candidates is not a new investment pipeline. It is a pre-pipeline work queue that hands off to the existing `review_needed` triage and deal pipeline when a company deserves investment review.
- Ritchie can automate candidate status movement for clear meeting/review-needed signals, but every automatic move must be explainable and auditable.
- Unclear verification states should not disappear by default forever; they should be visible through filters and warnings so users can decide whether to pursue edge cases.

## Assumptions — Outreach Candidate Score

- The first scoring rubric is intentionally provisional and should be easy to tune after real use.
- The score should make the list easier to work, not replace judgment. Manual status/priority overrides remain available.
- Explainability matters more than mathematical sophistication in v1.3.
- Missing evidence should be visible in the score breakdown so users know whether a low score reflects weak fit or incomplete data.

## Assumptions — Thesis/Rubric-Aware Candidate Scoring

- `reference_files/"1829 Ventures Screening Rubric.pdf"` and `reference_files/"1829 Ventures Investment Thesis v2.7.docx"` are the authoritative local source docs for v1.3 scoring.
- Rubric/thesis scoring is an aid for prioritization, not an automatic investment decision.
- A slightly higher fit score should break ties between otherwise similar candidates, but users can manually override candidate priority/status.
- Source-doc changes should make prior scores stale until refreshed.

## Assumptions — LinkedIn Message Memory

- LinkedIn access is read-only in v1.3. The CRM must not send, delete, archive, mark read/unread, or otherwise mutate LinkedIn messages.
- Ritchie may create CRM follow-up tasks based on LinkedIn messages without user approval, because those tasks are internal CRM records that can be dismissed or edited. This does not violate the read-only LinkedIn constraint.
- LinkedIn message data may arrive from an export or connector; the implementation should preserve read-only provenance either way.
- The goal is durable recall: users should not need to remember that a company/person already appeared in LinkedIn messages.
- Ambiguous CRM matches are acceptable as long as uncertainty is visible and reviewable.
- Ritchie-created tasks should always have clear visual provenance, including a tiger logo or tiger-style badge in the top-right of the task surface.
- Low-value task filtering is intentionally left adjustable after v1.3 usage. Duplicate prevention is required now; preference tuning can come later.

## Assumptions — Email and Calendar Memory Boundaries

- Ritchie can process email only when intentionally included via Bcc or an equivalent explicit-copy workflow.
- v1.3 should not give Ritchie general mailbox visibility.
- Calendar access may be considered later, but is not enabled in v1.3.
- Relationship memory should make source boundaries obvious so users know whether context came from LinkedIn, Bcc email, CRM interactions, or a future calendar integration.

## Assumptions — RIT Alumni Founder Verification

- Dealroom founder university data is accurate enough to seed RIT alumni-founder candidates.
- Dealroom does not reliably prove whether the founder is still active at the company, so Ritchie should check the Dealroom-provided LinkedIn URL before the company is treated as outreach-ready.
- LinkedIn evidence can be incomplete or inaccessible. v1.3 records confidence and evidence rather than requiring human confirmation.
- The first target stage range is pre-seed through Series A.
- "Operational" needs a CRM-side filter even when Dealroom claims a company is active, because many imported companies may no longer be operating.

## Assumptions — Operational Status Verification

- Dealroom operational status is useful input but not authoritative.
- Ritchie can make a useful confidence-scored operational assessment from lightweight public signals such as a live website, LinkedIn/company activity, founder current roles, and obvious shutdown/dead-domain signals.
- v1.3 does not need a perfect company-liveness classifier. It needs a practical filter that improves outreach list quality and makes uncertainty visible.
- Operational verification should be refreshable because company status can change and stale evidence should degrade confidence over time.

## Assumptions — MCP + Ritchie/kernelbot

- The MCP server will evolve alongside the product during this mini-sprint rather than waiting for a separate integration pass.
- Ritchie/kernelbot is not a privileged backdoor. It can only do what the MCP tools and CRM permission model allow.

## Potential Future Features (v1.3 and beyond)

- News tab for portfolio companies: aggregate company-related news, show source/date/headline/summary, and eventually let Ritchie summarize relevant developments. This is explicitly not a v1.3 priority.
- Full-text extraction and search indexing of document contents (PDF via `pypdf`/`pdfplumber`, DOCX via `python-docx`, XLSX via the already-installed `openpyxl`), feeding both the keyword `tsvector` index and the semantic/RAG layer so Ritchie can answer questions grounded in uploaded documents.
- Document versioning (explicit "supersedes" relationship when a file with the same name is re-uploaded, instead of two unrelated rows).
- Task-level document attachments.
- In-app preview for Office formats (currently out of scope; PDF gets a native browser preview via the presigned URL, `.md`/`.csv` are cheap to render in-app, `.docx`/`.xlsx` are download-only in v1.3).
- Antivirus/malware scanning if the upload surface ever becomes broader than the internal team.
- Explicit hard-purge/retention job using the new `delete_object` capability, for archived documents past a retention window.
- Richer Ritchie workflows after the MCP foundation is stable: proactive follow-up reminders, company brief generation, document Q&A, and news summarization.
- Richer alumni-founder enrichment: multiple-school filters, founder employment-history timelines, auto-refresh schedules, and relationship-path suggestions beyond the initial RIT workflow.
- Richer operational intelligence: scheduled re-verification, traffic/product-signal checks, funding/news-based liveness signals, and automated stale-company cleanup queues.
- Campaign-style sequencing, email template management, deliverability tracking, and bulk-send automation for candidate lists.
- Deeper score calibration: historical investment outcomes, partner feedback loops, and configurable scoring weights by thesis area.
- LinkedIn write workflows such as drafting/sending messages, marking conversations, syncing read state, or automated follow-up campaigns.
- Calendar relationship memory: meetings, attendees, meeting notes, and missed follow-up detection after calendar access is explicitly permitted.
