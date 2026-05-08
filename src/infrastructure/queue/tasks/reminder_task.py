"""Celery beat task: scan for overdue obligations and send reminders."""
from __future__ import annotations

import asyncio

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.reminder_task.scan_overdue_obligations",
    queue="clm.maintenance",
)
def scan_overdue_obligations() -> dict:
    return asyncio.run(_async_scan())


async def _async_scan() -> dict:
    from datetime import UTC, datetime, timedelta
    from src.infrastructure.database.session import async_session_factory
    from sqlalchemy import select, and_
    from src.infrastructure.database.models.contract_obligation_model import ContractObligationModel

    now = datetime.now(UTC)
    window_end = now + timedelta(days=7)
    notified = 0

    async with async_session_factory() as session:
        result = await session.execute(
            select(ContractObligationModel).where(
                and_(
                    ContractObligationModel.status == "OPEN",
                    ContractObligationModel.due_date <= window_end,
                    ContractObligationModel.due_date >= now,
                )
            )
        )
        obligations = result.scalars().all()

        # Send notifications for each upcoming obligation
        from src.infrastructure.notifications.webhook_notifier import WebhookNotifier

        try:
            notifier = WebhookNotifier()
        except Exception:
            notifier = None

        for ob in obligations:
            log.info(
                "reminder.due_soon",
                obligation_id=str(ob.id),
                title=ob.title,
                due_date=str(ob.due_date),
            )
            if notifier:
                try:
                    await notifier.notify_obligation_due(
                        obligation_id=ob.id,
                        title=ob.title or "Untitled obligation",
                        due_date=ob.due_date,
                        contract_id=ob.contract_id,
                    )
                except Exception as exc:
                    log.warning("reminder.notify_failed", error=str(exc), obligation_id=str(ob.id))
            notified += 1

    log.info("reminder.scan_complete", notified=notified)
    return {"notified": notified}
