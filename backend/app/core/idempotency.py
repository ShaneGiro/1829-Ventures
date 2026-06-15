"""Idempotency-key construction for Ritchie's writes.

Every authorized agent write carries a stable key derived from the event ID, the
tool name, and the target entity ID. The key is unique-constrained on
`ai_audit_logs.idempotency_key`, so a duplicate event/tool/entity combination is
a no-op rather than a double-write.
"""

from __future__ import annotations

import hashlib


def build_idempotency_key(event_id: str, tool: str, entity_id: str | None) -> str:
    """Deterministic key for (event, tool, entity). Stable across retries."""
    raw = f"{event_id}|{tool}|{entity_id or '-'}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{tool}:{digest[:32]}"
