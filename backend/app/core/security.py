"""Security primitives: JWT signing/verification and API-key hashing.

Uses PyJWT (actively maintained) rather than python-jose. Passwordless auth only —
human users authenticate via Google OAuth; Ritchie uses a hashed scoped API key.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Sign a JWT for an authenticated human user."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expires_minutes or settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Verify and decode a JWT, raising AuthenticationError on any failure."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid token") from exc


# ─── API keys (Ritchie) ───────────────────────────────────────────────────────
def generate_api_key() -> str:
    """Generate a new opaque API key. Store only its hash."""
    return secrets.token_urlsafe(48)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage/comparison (SHA-256, no salt needed for high-entropy keys)."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    """Constant-time comparison of a presented key against the stored hash."""
    return hmac.compare_digest(hash_api_key(api_key), expected_hash)
