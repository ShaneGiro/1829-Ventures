"""SendGrid email adapter for transactional notifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class EmailDeliveryResult:
    provider_message_id: str | None
    status_code: int | None


class SendGridEmailClient:
    def __init__(self, *, api_key: str, from_address: str) -> None:
        self.api_key = api_key
        self.from_address = from_address

    def send_email(self, *, to_email: str, subject: str, html_body: str) -> EmailDeliveryResult:
        if not self.api_key:
            return EmailDeliveryResult(provider_message_id=None, status_code=None)

        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=self.from_address,
            to_emails=to_email,
            subject=subject,
            html_content=html_body,
        )
        response: Any = SendGridAPIClient(self.api_key).send(message)
        message_id = None
        headers = getattr(response, "headers", None)
        if headers is not None:
            message_id = headers.get("X-Message-Id") or headers.get("x-message-id")
        return EmailDeliveryResult(
            provider_message_id=message_id,
            status_code=int(response.status_code),
        )


def get_email_client() -> SendGridEmailClient:
    return SendGridEmailClient(
        api_key=settings.sendgrid_api_key,
        from_address=settings.email_from_address,
    )
