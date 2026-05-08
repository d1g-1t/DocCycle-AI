"""Celery application factory."""
from __future__ import annotations

from celery import Celery

from src.core.config import get_settings


def create_celery_app() -> Celery:
    s = get_settings()
    app = Celery(
        "contractforge",
        broker=s.redis_url,
        backend=s.redis_url.replace("/0", "/1"),
        include=[
            "src.infrastructure.queue.tasks.ai_review_task",
            "src.infrastructure.queue.tasks.obligation_extraction_task",
            "src.infrastructure.queue.tasks.embedding_task",
            "src.infrastructure.queue.tasks.reminder_task",
            "src.infrastructure.queue.tasks.parse_uploaded_contract_task",
            "src.infrastructure.queue.tasks.negotiation_summary_task",
            "src.infrastructure.queue.tasks.workflow_sla_monitor_task",
            "src.infrastructure.queue.tasks.analytics_refresh_task",
            "src.infrastructure.queue.tasks.cleanup_orphan_files_task",
        ],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "*.ai_review_task.*": {"queue": "clm.ai"},
            "*.obligation_extraction_task.*": {"queue": "clm.ai"},
            "*.negotiation_summary_task.*": {"queue": "clm.ai"},
            "*.embedding_task.*": {"queue": "clm.analytics"},
            "*.analytics_refresh_task.*": {"queue": "clm.analytics"},
            "*.parse_uploaded_contract_task.*": {"queue": "clm.parse"},
            "*.workflow_sla_monitor_task.*": {"queue": "clm.workflow"},
            "*.reminder_task.*": {"queue": "clm.maintenance"},
            "*.cleanup_orphan_files_task.*": {"queue": "clm.maintenance"},
        },
        beat_schedule={
            "scan-overdue-obligations": {
                "task": "src.infrastructure.queue.tasks.reminder_task.scan_overdue_obligations",
                "schedule": 3600.0,  # every hour
            },
            "check-sla-breaches": {
                "task": "src.infrastructure.queue.tasks.workflow_sla_monitor_task.check_sla_breaches",
                "schedule": 900.0,  # every 15 minutes
            },
            "refresh-analytics": {
                "task": "src.infrastructure.queue.tasks.analytics_refresh_task.refresh_analytics",
                "schedule": 1800.0,  # every 30 minutes
            },
            "cleanup-orphan-files": {
                "task": "src.infrastructure.queue.tasks.cleanup_orphan_files_task.cleanup_orphan_files",
                "schedule": 86400.0,  # daily
            },
        },
    )
    return app


celery_app = create_celery_app()
