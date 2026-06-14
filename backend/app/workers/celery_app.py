"""Celery application bootstrap.

Workers use the SYNC SQLAlchemy engine (psycopg2) — never the async engine.
Job modules are registered via `include` as later agents add them. Retry defaults
support the graceful-degradation requirement (agent jobs retry with backoff).
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ventures_crm",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.jobs.dealroom_import_jobs",
        "app.workers.jobs.embedding_jobs",
        "app.workers.jobs.analytics_jobs",
        # Later agents append their job modules here, e.g.:
        # "app.workers.jobs.gmail_jobs",
        # "app.workers.jobs.agent_jobs",
        # "app.workers.jobs.notification_jobs",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.timezone,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=10,
    task_max_retries=5,
    result_expires=3600,
)


@celery_app.task(name="health.ping")
def ping() -> str:
    """Trivial task to verify the worker can pick up and run jobs."""
    return "pong"
