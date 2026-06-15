"""Forwarded Gmail ingestion service."""

from __future__ import annotations

import base64
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parseaddr, parsedate_to_datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.constants import DocumentSource, InteractionType, RelationshipStatus
from app.core.exceptions import ValidationError
from app.integrations.minio_storage import get_document_storage
from app.integrations.storage import DocumentStorage
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.user import User
from app.repositories import interactions as interaction_repo
from app.repositories.interactions import EmailMatch
from app.schemas.email import GmailForwardedEmailIngest, GmailIngestResult
from app.schemas.interaction import InteractionRead
from app.services import audit_service
from app.services.pipeline_service import mark_review_needed
from app.workers.jobs.embedding_jobs import embed_interactions

REVIEW_PARSE_FAILED = "parse_failed"
REVIEW_UNMATCHED = "unmatched"
REVIEW_MATCHED = "matched"
ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ParsedForwardedEmail:
    original_sender: str
    original_recipient: str | None
    original_date: datetime | None
    subject: str
    content: str


def normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    _name, address = parseaddr(value.strip())
    return address.lower() or value.strip().lower()


def email_domain(email: str | None) -> str | None:
    normalized = normalize_email(email)
    if normalized is None or "@" not in normalized:
        return None
    return normalized.rsplit("@", 1)[1]


def parse_forwarded_message(raw_message: str) -> ParsedForwardedEmail:
    gmail = _parse_gmail_forward(raw_message)
    if gmail is not None:
        return gmail
    outlook = _parse_outlook_forward(raw_message)
    if outlook is not None:
        return outlook
    raise ValidationError("Forwarded email format could not be parsed")


async def ingest_forwarded_email(
    session: AsyncSession,
    payload: GmailForwardedEmailIngest,
    *,
    actor: User,
    storage: DocumentStorage | None = None,
) -> GmailIngestResult:
    interaction = Interaction(
        interaction_type=InteractionType.EMAIL,
        summary="Forwarded email pending parse",
        body=payload.raw_message,
        occurred_at=payload.received_at or datetime.now(UTC),
        source_email_id=payload.source_email_id,
        forwarded_by=payload.forwarded_by.lower(),
        provenance={
            "source": "gmail_forward",
            "raw_stored_at": datetime.now(UTC).isoformat(),
            "review_status": "received",
            "forwarded_by": payload.forwarded_by.lower(),
        },
    )
    await interaction_repo.create_interaction(session, interaction)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=interaction)
    await session.commit()
    await session.refresh(interaction)

    try:
        parsed = parse_forwarded_message(payload.raw_message)
    except ValidationError as exc:
        await _mark_for_review(session, interaction, REVIEW_PARSE_FAILED, str(exc))
        return GmailIngestResult(
            status=REVIEW_PARSE_FAILED,
            interaction=InteractionRead.model_validate(interaction),
            review_reason=str(exc),
        )

    match = await interaction_repo.find_email_match(session, parsed.original_sender)
    document_ids = await _store_attachment_metadata(
        session,
        payload,
        interaction=interaction,
        match=match,
        actor=actor,
        storage=storage,
    )

    interaction.original_sender = parsed.original_sender
    interaction.original_recipient = parsed.original_recipient
    interaction.occurred_at = parsed.original_date or interaction.occurred_at
    interaction.summary = parsed.subject
    interaction.body = parsed.content
    interaction.company_id = match.company_id
    interaction.person_id = match.person_id
    interaction.provenance = {
        **interaction.provenance,
        "original_sender": parsed.original_sender,
        "original_recipient": parsed.original_recipient,
        "original_date": parsed.original_date.isoformat() if parsed.original_date else None,
        "attachment_count": len(payload.attachments),
        "stored_attachment_count": len(document_ids),
        "review_status": (
            REVIEW_MATCHED if match.company_id or match.person_id else REVIEW_UNMATCHED
        ),
    }

    if match.company_id is None and match.person_id is None:
        await session.commit()
        await session.refresh(interaction)
        return GmailIngestResult(
            status=REVIEW_UNMATCHED,
            interaction=InteractionRead.model_validate(interaction),
            document_ids=document_ids,
            review_reason="No deterministic company or person match found",
        )

    if match.company_id is not None:
        company = await interaction_repo.get_company_for_email_ingestion(session, match.company_id)
        if company is not None and company.relationship_status == RelationshipStatus.CONTACTED:
            await mark_review_needed(session, company_id=company.id, owner_id=actor.id)
        else:
            await session.commit()
    else:
        await session.commit()

    await session.refresh(interaction)
    embed_interactions.delay([str(interaction.id)])
    return GmailIngestResult(
        status=REVIEW_MATCHED,
        interaction=InteractionRead.model_validate(interaction),
        document_ids=document_ids,
    )


async def _mark_for_review(
    session: AsyncSession,
    interaction: Interaction,
    status: str,
    reason: str,
) -> None:
    interaction.provenance = {
        **interaction.provenance,
        "review_status": status,
        "review_reason": reason,
    }
    await session.commit()
    await session.refresh(interaction)


async def _store_attachment_metadata(
    session: AsyncSession,
    payload: GmailForwardedEmailIngest,
    *,
    interaction: Interaction,
    match: EmailMatch,
    actor: User,
    storage: DocumentStorage | None,
) -> list[uuid.UUID]:
    document_ids: list[uuid.UUID] = []
    storage_client = storage or get_document_storage()
    for attachment in payload.attachments:
        metadata = {
            "source_email_id": payload.source_email_id,
            "forwarded_by": payload.forwarded_by.lower(),
            "interaction_id": str(interaction.id),
            "storage_status": "metadata_only",
        }
        storage_key: str | None = None
        if attachment.content_base64 and attachment.size_bytes <= ATTACHMENT_MAX_BYTES:
            storage_key = f"email-attachments/{payload.source_email_id}/{attachment.filename}"
            storage_client.put_object(
                storage_key=storage_key,
                body=base64.b64decode(attachment.content_base64),
                content_type=attachment.content_type,
            )
            metadata["storage_status"] = "stored"
        elif attachment.size_bytes > ATTACHMENT_MAX_BYTES:
            metadata["storage_status"] = "skipped_size_limit"

        document = Document(
            filename=attachment.filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            storage_key=storage_key,
            source=DocumentSource.EMAIL,
            company_id=match.company_id,
            person_id=match.person_id,
            uploaded_by=actor.id,
            extra_metadata=metadata,
        )
        session.add(document)
        await session.flush()
        document_ids.append(document.id)
    return document_ids


def _parse_gmail_forward(raw_message: str) -> ParsedForwardedEmail | None:
    if "---------- Forwarded message ---------" not in raw_message:
        return None
    header, content = raw_message.split("---------- Forwarded message ---------", 1)
    _ = header
    return _parse_header_block(content)


def _parse_outlook_forward(raw_message: str) -> ParsedForwardedEmail | None:
    markers = ("-----Original Message-----", "From:")
    if not any(marker in raw_message for marker in markers):
        return None
    content = raw_message
    if "-----Original Message-----" in raw_message:
        _prefix, content = raw_message.split("-----Original Message-----", 1)
    return _parse_header_block(content)


def _parse_header_block(block: str) -> ParsedForwardedEmail:
    fields = _extract_forward_headers(block)
    sender = normalize_email(fields.get("from"))
    if sender is None:
        raise ValidationError("Forwarded email is missing original sender")
    subject = fields.get("subject") or "(no subject)"
    recipient = normalize_email(fields.get("to"))
    date_value = _parse_forwarded_date(fields.get("date") or fields.get("sent"))
    body = _strip_forward_headers(block).strip()
    if not body:
        body = subject
    return ParsedForwardedEmail(
        original_sender=sender,
        original_recipient=recipient,
        original_date=date_value,
        subject=subject.strip(),
        content=body,
    )


def _extract_forward_headers(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            if fields:
                break
            continue
        match = re.match(r"^(From|To|Date|Sent|Subject):\s*(.+)$", stripped, re.IGNORECASE)
        if match:
            fields[match.group(1).lower()] = match.group(2).strip()
    return fields


def _strip_forward_headers(block: str) -> str:
    lines = block.splitlines()
    body_start = 0
    seen_header = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^(From|To|Date|Sent|Subject):\s*", stripped, re.IGNORECASE):
            seen_header = True
            body_start = index + 1
            continue
        if seen_header and not stripped:
            body_start = index + 1
            break
    return "\n".join(lines[body_start:])


def _parse_forwarded_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
