"""Config smoke tests: the dual-driver URL derivation works as documented."""

from __future__ import annotations

from app.core.config import Settings


def test_async_and_sync_urls_use_correct_drivers() -> None:
    settings = Settings(database_url="postgresql://u:p@host:5432/db")
    assert settings.async_database_url == "postgresql+asyncpg://u:p@host:5432/db"
    assert settings.sync_database_url == "postgresql+psycopg2://u:p@host:5432/db"


def test_allowed_domains_parsed_from_csv() -> None:
    settings = Settings(allowed_email_domains="g.rit.edu, rit.edu")
    assert settings.allowed_domains_list == ["g.rit.edu", "rit.edu"]
