from __future__ import annotations

from typing import Any

import pytest

from app.core.config import settings
from app.integrations import ritchie_client


def test_deliver_envelope_posts_kernelbot_scheduler_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> Response:
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(settings, "ritchie_webhook_url", "http://kernelbot-scheduler:3003/schedule")
    monkeypatch.setattr(settings, "ritchie_scheduler_tag", "1829-crm")
    monkeypatch.setattr(settings, "ritchie_scheduler_model", "sonnet")
    monkeypatch.setattr(settings, "ritchie_scheduler_max_retries", 1)
    monkeypatch.setattr(ritchie_client.httpx, "post", fake_post)

    envelope = {"id": "evt-1", "event_type": "human_prompt", "payload": {"prompt": "research"}}

    ritchie_client.deliver_envelope(envelope, timeout=3.0)

    assert captured["url"] == "http://kernelbot-scheduler:3003/schedule"
    assert captured["json"] == {
        "tag": "1829-crm",
        "envelope": envelope,
        "model": "sonnet",
        "max_retries": 1,
    }
    assert captured["headers"] == {"Content-Type": "application/json"}
    assert captured["timeout"] == 3.0


def test_deliver_envelope_noops_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_post(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("httpx.post should not be called")

    monkeypatch.setattr(settings, "ritchie_webhook_url", "")
    monkeypatch.setattr(ritchie_client.httpx, "post", fail_post)

    ritchie_client.deliver_envelope({"id": "evt-1"})


def test_chat_with_ritchie_posts_waiting_invoke(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {"summary": "Created the follow-up task.", "exit": 0, "elapsed_ms": 1234}

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str],
        timeout: float,
    ) -> Response:
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(settings, "ritchie_chat_url", "http://kernelbot-admin:8080/invoke?wait=true")
    monkeypatch.setattr(settings, "ritchie_chat_timeout_seconds", 30.0)
    monkeypatch.setattr(ritchie_client.httpx, "post", fake_post)

    result = ritchie_client.chat_with_ritchie({"id": "evt-1"}, timeout=12.0)

    assert result["summary"] == "Created the follow-up task."
    assert captured["url"] == "http://kernelbot-admin:8080/invoke?wait=true"
    assert captured["json"] == {
        "trigger": "crm_chat",
        "envelope": {"id": "evt-1"},
        "timeout_ms": 12000,
    }
    assert captured["headers"] == {"Content-Type": "application/json"}
    assert captured["timeout"] == 22.0
