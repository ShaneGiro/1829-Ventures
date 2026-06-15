"""Celery jobs for Gmail ingestion follow-up work."""

from __future__ import annotations

from app.workers.celery_app import celery_app
from app.workers.jobs.embedding_jobs import embed_interactions


@celery_app.task(name="gmail.embed_interaction")
def embed_gmail_interaction(interaction_id: str) -> None:
    embed_interactions.delay([interaction_id])
