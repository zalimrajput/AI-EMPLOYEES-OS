"""Celery application for background tasks.

Broker: Redis configured via ``REDIS_URL``. Tasks live in ``workers/`` and are
imported at app configuration time so ``celery -A workers.celery_app worker``
discovers them automatically.
"""
import os

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "ai_employee_os",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.email_worker",
        "workers.notification_worker",
        "workers.embedding_worker",
        "workers.document_worker",
        "workers.report_worker",
        "workers.whatsapp_worker",
        "workers.ai_worker",
        "workers.followup_worker",
        "workers.recurring_invoice_worker",
    ],
)

celery_app.conf.beat_schedule = {
    "check-stale-sales-threads": {
        "task": "workers.check_stale_customer_threads",
        "schedule": crontab(minute=0),
    },
    "generate-due-recurring-invoices": {
        "task": "workers.generate_due_recurring_invoices",
        "schedule": crontab(hour=1, minute=0),
    },
}

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)