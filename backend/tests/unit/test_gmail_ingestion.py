"""Forwarded Gmail ingestion tests."""

from __future__ import annotations

import base64
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.constants import RelationshipStatus, Role
from app.core.exceptions import ValidationError
from app.models.company import Company
from app.models.interaction import Interaction
from app.models.user import User
from app.repositories import interactions as interaction_repo
from app.repositories.interactions import (
    EmailMatch,
    score_company_candidate,
    suggest_company_match,
)
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
    # Provenance records both the forwarding team member and the original sender.
    assert result.interaction.forwarded_by == "analyst@g.rit.edu"
    assert result.interaction.original_sender == "jane@startup.com"
    assert result.interaction.provenance["forwarded_by"] == "analyst@g.rit.edu"


def _patch_common(monkeypatch: pytest.MonkeyPatch) -> None:
    async def create_interaction(_session: FakeSession, interaction: Interaction) -> Interaction:
        _session.add(interaction)
        await _session.flush()
        return interaction

    async def record_create(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(service.interaction_repo, "create_interaction", create_interaction)
    monkeypatch.setattr(service.audit_service, "record_create", record_create)
    monkeypatch.setattr(service.embed_interactions, "delay", lambda *_args: None)


@pytest.mark.asyncio
async def test_unmatched_forward_routes_to_review(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    _patch_common(monkeypatch)

    async def find_email_match(_session: FakeSession, _sender: str) -> EmailMatch:
        return EmailMatch()

    async def no_suggestion(_session: FakeSession, _sender: str) -> None:
        return None

    monkeypatch.setattr(service.interaction_repo, "find_email_match", find_email_match)
    monkeypatch.setattr(service.interaction_repo, "suggest_company_match", no_suggestion)

    result = await service.ingest_forwarded_email(
        session,  # type: ignore[arg-type]
        GmailForwardedEmailIngest(
            source_email_id="msg-3",
            forwarded_by="analyst@g.rit.edu",
            raw_message=gmail_forward(),
        ),
        actor=make_actor(),
        storage=FakeStorage(),  # type: ignore[arg-type]
    )

    assert result.status == service.REVIEW_UNMATCHED
    assert result.interaction.company_id is None
    assert result.interaction.person_id is None
    assert "fuzzy_suggestion" not in result.interaction.provenance


@pytest.mark.asyncio
async def test_unmatched_forward_includes_fuzzy_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    _patch_common(monkeypatch)
    suggested_company_id = uuid.uuid4()

    async def find_email_match(_session: FakeSession, _sender: str) -> EmailMatch:
        return EmailMatch()

    async def suggest(
        _session: FakeSession, sender: str
    ) -> interaction_repo.FuzzyCompanySuggestion:
        assert sender == "jane@startup.com"
        return interaction_repo.FuzzyCompanySuggestion(
            company_id=suggested_company_id,
            company_name="Startup Labs",
            confidence=0.82,
            reason="domain match",
        )

    monkeypatch.setattr(service.interaction_repo, "find_email_match", find_email_match)
    monkeypatch.setattr(service.interaction_repo, "suggest_company_match", suggest)

    result = await service.ingest_forwarded_email(
        session,  # type: ignore[arg-type]
        GmailForwardedEmailIngest(
            source_email_id="msg-4",
            forwarded_by="analyst@g.rit.edu",
            raw_message=gmail_forward(),
        ),
        actor=make_actor(),
        storage=FakeStorage(),  # type: ignore[arg-type]
    )

    assert result.status == service.REVIEW_UNMATCHED
    # Suggestion is surfaced but the company is NOT auto-attached.
    assert result.interaction.company_id is None
    suggestion = result.interaction.provenance["fuzzy_suggestion"]
    assert suggestion["company_id"] == str(suggested_company_id)
    assert suggestion["company_name"] == "Startup Labs"
    assert "Startup Labs" in (result.review_reason or "")


@pytest.mark.asyncio
async def test_oversized_attachment_is_not_stored(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    storage = FakeStorage()
    _patch_common(monkeypatch)
    company_id = uuid.uuid4()

    async def find_email_match(_session: FakeSession, _sender: str) -> EmailMatch:
        return EmailMatch(company_id=company_id)

    async def no_company(*_args: object) -> None:
        return None

    monkeypatch.setattr(service.interaction_repo, "find_email_match", find_email_match)
    monkeypatch.setattr(service.interaction_repo, "get_company_for_email_ingestion", no_company)

    result = await service.ingest_forwarded_email(
        session,  # type: ignore[arg-type]
        GmailForwardedEmailIngest(
            source_email_id="msg-5",
            forwarded_by="analyst@g.rit.edu",
            raw_message=gmail_forward(),
            attachments=[
                ForwardedEmailAttachment(
                    filename="huge.zip",
                    content_type="application/zip",
                    size_bytes=service.ATTACHMENT_MAX_BYTES + 1,
                    content_base64=base64.b64encode(b"x").decode("ascii"),
                )
            ],
        ),
        actor=make_actor(),
        storage=storage,  # type: ignore[arg-type]
    )

    assert result.status == service.REVIEW_MATCHED
    # Nothing was uploaded; the document metadata records the skip reason.
    assert storage.objects == []
    documents = [obj for obj in session.added if type(obj).__name__ == "Document"]
    assert len(documents) == 1
    assert documents[0].storage_key is None
    assert documents[0].extra_metadata["storage_status"] == "skipped_size_limit"


@pytest.mark.asyncio
async def test_founder_reply_moves_contacted_company_to_review_needed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    _patch_common(monkeypatch)
    company_id = uuid.uuid4()
    calls: list[uuid.UUID] = []

    async def find_email_match(_session: FakeSession, _sender: str) -> EmailMatch:
        return EmailMatch(company_id=company_id)

    async def get_company(_session: FakeSession, cid: uuid.UUID) -> Company:
        return Company(id=cid, name="Startup", relationship_status=RelationshipStatus.CONTACTED)

    async def mark_review_needed(
        _session: FakeSession, *, company_id: uuid.UUID, owner_id: object
    ) -> None:
        calls.append(company_id)

    monkeypatch.setattr(service.interaction_repo, "find_email_match", find_email_match)
    monkeypatch.setattr(service.interaction_repo, "get_company_for_email_ingestion", get_company)
    monkeypatch.setattr(service, "mark_review_needed", mark_review_needed)

    result = await service.ingest_forwarded_email(
        session,  # type: ignore[arg-type]
        GmailForwardedEmailIngest(
            source_email_id="msg-6",
            forwarded_by="analyst@g.rit.edu",
            raw_message=gmail_forward(),
        ),
        actor=make_actor(),
        storage=FakeStorage(),  # type: ignore[arg-type]
    )

    assert result.status == service.REVIEW_MATCHED
    assert calls == [company_id]


def test_score_company_candidate_threshold() -> None:
    # Domain root close to the company name scores high; unrelated scores low.
    assert score_company_candidate("startup", name="Startup Labs", domain="startup.com") >= 0.6
    assert score_company_candidate("startup", name="Acme Robotics", domain="acme.io") < 0.6


@pytest.mark.asyncio
async def test_suggest_company_match_ranks_best_candidate() -> None:
    matching_id = uuid.uuid4()

    class ScalarSession:
        async def scalars(self, _stmt: object) -> list[Company]:
            return [
                Company(id=uuid.uuid4(), name="Acme Robotics", domain="acme.io"),
                Company(id=matching_id, name="Startup Labs", domain="startup.com"),
            ]

    suggestion = await suggest_company_match(ScalarSession(), "jane@startup.com")  # type: ignore[arg-type]
    assert suggestion is not None
    assert suggestion.company_id == matching_id
    assert suggestion.confidence >= 0.6


@pytest.mark.asyncio
async def test_suggest_company_match_short_root_returns_none() -> None:
    class ScalarSession:
        async def scalars(self, _stmt: object) -> list[Company]:  # pragma: no cover - not reached
            return []

    # Single-char domain root is below the minimum length; no query is run.
    assert await suggest_company_match(ScalarSession(), "x@a.com") is None
