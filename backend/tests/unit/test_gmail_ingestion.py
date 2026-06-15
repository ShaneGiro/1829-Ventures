"""Forwarded Gmail ingestion tests."""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.constants import Role
from app.core.exceptions import ValidationError
from app.models.interaction import Interaction
from app.models.user import User
from app.repositories.interactions import EmailMatch
from app.schemas.email import ForwardedEmailAttachment, GmailForwardedEmailIngest
from app.services import gmail_ingestion_service as service


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.added: list[Any] = []

    def add(self, value: Any) -> None:
        if getattr(value, "id", None) is None:
            value.id = uuid.uuid4()
        self.added.append(value)

    async def flush(self) -> None:
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid.uuid4()

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, value: Any) -> None:
        if getattr(value, "id", None) is None:
            value.id = uuid.uuid4()
        now = datetime.now(UTC)
        if getattr(value, "created_at", None) is None:
            value.created_at = now
        if getattr(value, "updated_at", None) is None:
            value.updated_at = now


class FakeStorage:
    def __init__(self) -> None:
        self.objects: list[tuple[str, bytes, str | None]] = []

    def put_object(self, *, storage_key: str, body: bytes, content_type: str | None) -> None:
        self.objects.append((storage_key, body, content_type))


def make_actor() -> User:
    return User(
        id=uuid.uuid4(),
        email="analyst@g.rit.edu",
        role=Role.MEMBER,
        is_active=True,
        is_agent=False,
    )


def gmail_forward() -> str:
    return """FYI

---------- Forwarded message ---------
From: Jane Founder <jane@startup.com>
Date: Mon, 10 Jun 2026 10:15:00 -0400
Subject: Re: 1829 intro
To: Analyst <analyst@g.rit.edu>

Thanks for reaching out. Happy to chat next week.
"""


def outlook_forward() -> str:
    return """Forwarded from Outlook

-----Original Message-----
From: Alex Founder <alex@example.com>
Sent: Tuesday, June 11, 2026 2:30 PM
To: Analyst <analyst@g.rit.edu>
Subject: Pitch deck

Please see attached.
"""


def test_parse_gmail_forward() -> None:
    parsed = service.parse_forwarded_message(gmail_forward())
    assert parsed.original_sender == "jane@startup.com"
    assert parsed.original_recipient == "analyst@g.rit.edu"
    assert parsed.subject == "Re: 1829 intro"
    assert "Happy to chat" in parsed.content


def test_parse_outlook_forward() -> None:
    parsed = service.parse_forwarded_message(outlook_forward())
    assert parsed.original_sender == "alex@example.com"
    assert parsed.subject == "Pitch deck"
    assert "Please see attached" in parsed.content


def test_parse_failure_is_validation_error() -> None:
    with pytest.raises(ValidationError):
        service.parse_forwarded_message("not a recognizable forward")


@pytest.mark.asyncio
async def test_parse_failure_keeps_raw_interaction_for_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()

    async def create_interaction(_session: FakeSession, interaction: Interaction) -> Interaction:
        _session.add(interaction)
        await _session.flush()
        return interaction

    async def record_create(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(service.interaction_repo, "create_interaction", create_interaction)
    monkeypatch.setattr(service.audit_service, "record_create", record_create)

    result = await service.ingest_forwarded_email(
        session,  # type: ignore[arg-type]
        GmailForwardedEmailIngest(
            source_email_id="msg-1",
            forwarded_by="analyst@g.rit.edu",
            raw_message="bad forward",
        ),
        actor=make_actor(),
    )

    assert result.status == service.REVIEW_PARSE_FAILED
    assert result.review_reason is not None
    assert result.interaction.body == "bad forward"


@pytest.mark.asyncio
async def test_matched_forward_creates_interaction_and_stores_small_attachment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    storage = FakeStorage()
    company_id = uuid.uuid4()
    person_id = uuid.uuid4()

    async def create_interaction(_session: FakeSession, interaction: Interaction) -> Interaction:
        _session.add(interaction)
        await _session.flush()
        return interaction

    async def record_create(*_args: object, **_kwargs: object) -> None:
        return None

    async def find_email_match(_session: FakeSession, sender_email: str) -> EmailMatch:
        assert sender_email == "jane@startup.com"
        return EmailMatch(company_id=company_id, person_id=person_id)

    async def no_company(*_args: object) -> None:
        return None

    monkeypatch.setattr(service.interaction_repo, "create_interaction", create_interaction)
    monkeypatch.setattr(service.audit_service, "record_create", record_create)
    monkeypatch.setattr(service.interaction_repo, "find_email_match", find_email_match)
    monkeypatch.setattr(service.interaction_repo, "get_company_for_email_ingestion", no_company)
    monkeypatch.setattr(service.embed_interactions, "delay", lambda *_args: None)

    result = await service.ingest_forwarded_email(
        session,  # type: ignore[arg-type]
        GmailForwardedEmailIngest(
            source_email_id="msg-2",
            forwarded_by="analyst@g.rit.edu",
            raw_message=gmail_forward(),
            attachments=[
                ForwardedEmailAttachment(
                    filename="deck.pdf",
                    content_type="application/pdf",
                    size_bytes=4,
                    content_base64=base64.b64encode(b"deck").decode("ascii"),
                )
            ],
        ),
        actor=make_actor(),
        storage=storage,  # type: ignore[arg-type]
    )

    assert result.status == service.REVIEW_MATCHED
    assert result.interaction.company_id == company_id
    assert result.interaction.person_id == person_id
    assert result.document_ids
    assert storage.objects[0][1] == b"deck"
