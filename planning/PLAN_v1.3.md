# 1829 Ventures CRM — v1.3 Plan

## Summary

v1.3 is the next release after v1 (see `planning/PLAN_v1.md`). This document is the working plan for v1.3 and will grow as additional v1.3 features are scoped — each feature gets its own subsection under the shared headings below (Data Model, API Surface, Frontend, Test Plan, Build Sequence) so the document stays organized by concern rather than by feature, matching `PLAN_v1.md`'s structure.

**First feature in scope: general-purpose file storage.** Users need to store and retrieve real files — pitch decks, memos, cap tables, data-room documents — attached to companies, deals, and people. PDF, Markdown, Excel (`.xlsx`), CSV, and Word (`.docx`) are the explicitly requested formats.

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
- Documents attach to a company, deal, and/or person, exactly as today. Task-level attachments are out of scope for v1.3 (see Potential Future Features).
- Allowed file types (extension + verified MIME/magic bytes, not just the client's declared `Content-Type`):
  - Documents: `.pdf`, `.md`, `.markdown`, `.txt`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.csv`.
  - Images (decks/screenshots/cap-table exports are often pasted as images): `.png`, `.jpg`, `.jpeg`.
  - The allowlist lives in one place (`app/core/constants.py`, `ALLOWED_DOCUMENT_EXTENSIONS`/`ALLOWED_DOCUMENT_MIME_TYPES`) so it can be extended without touching route/service code.
- Max upload size: 50 MB per file by default, configurable via `S3_MAX_UPLOAD_MB` env var. Large enough for a full pitch deck or data-room PDF; small enough that a 6 GB VM with a self-hosted MinIO doesn't get filled by a stray video upload.
- **Server verifies what actually landed in storage**, not what the client claims. After the browser completes the presigned POST, the frontend calls a new confirm endpoint; the backend does a `HeadObject` call against MinIO to read the real size and sniff the real content type from the first bytes (magic-byte check, not just trusting the extension), then rejects and deletes the object if it's oversized or not an allowed type. This closes the validation gap in item 5 above.
- Archiving a document soft-deletes the metadata row only (`archived_at`), consistent with the "never hard-delete" audit principle in `PLAN_v1.md`. The underlying object stays in MinIO. A `delete_object` capability is added to the storage protocol for a future explicit retention/purge job, but v1.3 does not call it automatically.
- Download is via a short-lived presigned GET URL (5 minute expiry), not a proxy through the API — keeps large file bytes off the FastAPI process, consistent with the upload design.
- v1.3 indexes **filenames only** into the existing Postgres full-text search (`tsvector`/GIN). Extracting and indexing the actual text content of PDFs/DOCX/XLSX is real scope (new parsing dependencies, background job, failure handling) and is deferred — see Potential Future Features.
- Ritchie's access to documents is unchanged by this plan: it already can read anything the CRM API exposes for a company/deal it has context on, and the existing Gmail-attachment path (`put_object`, trusted server-side write) is unaffected since the bug is isolated to the presigned-POST path.

## Data Model — File Storage

No new tables. Two additions to `backend/app/models/document.py` / the storage layer:

- `Document.status` (new column, `String(16)`, default `"pending"`): `pending` (row created, upload not yet confirmed) → `confirmed` (verified in storage) → `rejected` (failed validation, object deleted). Only `confirmed` documents are returned by default from `GET /documents` (mirrors how `include_archived` already filters).
- `PresignedUpload` dataclass (`app/integrations/storage.py`) gains a `fields: dict[str, str]` attribute so `generate_presigned_post`'s required form fields are no longer discarded. This is the core bug fix.
- `DocumentStorage` protocol gains two methods:
  - `create_presigned_download(*, storage_key: str, filename: str, expires_in: int = 300) -> str` — presigned GET URL, sets `ResponseContentDisposition` so the browser downloads with the original filename rather than the UUID-based storage key.
  - `head_object(*, storage_key: str) -> ObjectStat | None` — returns real `size_bytes` and sniffed `content_type` (via magic bytes) for the confirm step, or `None` if the object doesn't exist.
  - `delete_object(*, storage_key: str) -> None` — used by the confirm step on rejection, and reserved for a future purge job.

## API Surface — File Storage

Extends the existing `/documents` router (`backend/app/api/routes/documents.py`):

- `POST /documents/presigned-upload` (existing route, fixed): `PresignedUploadResponse` now also returns `fields: dict[str, str]` alongside `upload_url` and `storage_key`, so the frontend can build a correct multipart form POST.
- `POST /documents/{document_id}/confirm` (new): frontend calls this after the browser-to-MinIO upload completes. Backend calls `head_object`, validates size against `S3_MAX_UPLOAD_MB` and content type against the allowlist, sets `status="confirmed"` with the verified `size_bytes`/`content_type` on success, or `status="rejected"` + `delete_object` + a 422 response on failure.
- `GET /documents/{document_id}/download` (new): returns `{ "download_url": str, "expires_in": int }` — a presigned GET URL. Only `confirmed`, non-archived documents are downloadable (404 otherwise).
- Existing routes (`list`, `get`, `patch`, `archive`) unchanged in shape; `list_documents` gains an implicit filter to `status="confirmed"` unless the caller explicitly wants pending/rejected rows (admin/debug use only, not exposed in the frontend).

## Frontend — File Storage

- `frontend/src/api/documents.ts` gains:
  - `useCreatePresignedUpload()` — `POST /documents/presigned-upload`.
  - `useConfirmDocument()` — `POST /documents/{id}/confirm`.
  - `useDownloadDocument()` — `GET /documents/{id}/download`, opens the returned URL in a new tab.
  - `useArchiveDocument()` — `POST /documents/{id}/archive`, matching the existing `useArchiveDeal`/`useArchiveTask` convention.
- New `frontend/src/components/document/DocumentUploadZone.tsx` — drag-and-drop dropzone plus a click-to-browse fallback, mirroring the modal conventions already established in this codebase (`TaskCreateDialog.tsx`, `CloseInvestmentDialog.tsx`: controlled inputs, `Field` label wrapper, inline error text, disabled-while-pending buttons). Upload sequence: request presigned upload → `FormData` POST directly to MinIO with the returned `fields` + file → confirm → invalidate `["documents", ...]`. Client-side extension check gives instant feedback before the network round-trip; the server-side check in the confirm step remains the actual source of truth.
- `frontend/src/pages/CompanyDetail.tsx`'s existing "Documents" card is replaced with a real `DocumentList` component: file-type icon (lucide-react: `FileText` for pdf/docx/md/txt, `FileSpreadsheet` for xlsx/csv, `FileImage` for images), filename, size (human-readable), uploaded-by/at, a Download button, and an Archive button (with the same `ConfirmDialog` pattern used elsewhere for destructive-ish actions). The upload zone renders above the list.
- Same `DocumentList`/`DocumentUploadZone` components are written to accept either a `companyId` or `dealId` prop, so a future deal-level view can reuse them without changes.

## Test Plan — File Storage

- Unit tests:
  - `MinioDocumentStorage.create_presigned_upload` returns `fields` (regression test for the bug fix — assert the returned dict is non-empty and includes a policy field).
  - `head_object` correctly reports size and sniffs content type from magic bytes, independent of a spoofed extension.
  - Confirm-upload service logic: oversized file → `rejected` + object deleted; disallowed type → `rejected` + object deleted; valid file → `confirmed` with real size/content-type persisted.
  - Download endpoint 404s for `pending`/`rejected`/archived documents.
- Integration tests (against a real MinIO test bucket via the existing Docker Compose stack, or `moto`-mocked S3):
  - Full lifecycle: presigned-upload → direct upload to storage → confirm → download → archive.
  - Reject path: upload an executable renamed to `.pdf`, confirm it, assert `rejected` status and that the object no longer exists in the bucket.
- Acceptance scenario: upload a real `.pdf`, `.md`, `.xlsx`, `.csv`, and `.docx` from the company detail page, confirm each appears with the correct icon, download each and verify the bytes round-trip unchanged.

## Build Sequence — File Storage

1. Backend: fix `PresignedUpload`/`create_presigned_post` field passthrough; add `Document.status` column + migration; add `head_object`/`create_presigned_download`/`delete_object` to the storage protocol and MinIO adapter; add the confirm and download routes; add the allowlist constants and `S3_MAX_UPLOAD_MB` setting.
2. Backend: add `python-magic` for content-type sniffing (new dependency — requires `libmagic1` in the API/worker Docker image; update `backend/Dockerfile`).
3. Backend tests for the above.
4. Frontend: `documents.ts` mutation hooks, `DocumentUploadZone`, `DocumentList`, wire both into `CompanyDetail.tsx` in place of the current inert filename list.
5. Manual smoke test: upload/download/archive one file of each allowed type end-to-end via the running app.

## Assumptions — File Storage

- No AV/malware scanning engine (e.g. ClamAV) is introduced in v1.3. Magic-byte + extension allowlisting is the v1.3 defense; this is an internal-team tool behind RIT-Google-gated auth, not a public upload surface. Revisit if the threat model changes.
- `python-magic` requires the system `libmagic1` package — this is a new OS-level dependency for the API/worker containers, not just a Python package.
- Content-text extraction/indexing (PDF, DOCX, XLSX) and document versioning are both explicitly out of scope for this pass — see below.

## Potential Future Features (v1.3 and beyond)

- Full-text extraction and search indexing of document contents (PDF via `pypdf`/`pdfplumber`, DOCX via `python-docx`, XLSX via the already-installed `openpyxl`), feeding both the keyword `tsvector` index and the semantic/RAG layer so Ritchie can answer questions grounded in uploaded documents.
- Document versioning (explicit "supersedes" relationship when a file with the same name is re-uploaded, instead of two unrelated rows).
- Task-level document attachments.
- In-app preview for Office formats (currently out of scope; PDF gets a native browser preview via the presigned URL, `.md`/`.csv` are cheap to render in-app, `.docx`/`.xlsx` are download-only in v1.3).
- Antivirus/malware scanning if the upload surface ever becomes broader than the internal team.
- Explicit hard-purge/retention job using the new `delete_object` capability, for archived documents past a retention window.
