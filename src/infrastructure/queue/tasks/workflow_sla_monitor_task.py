"""Celery beat task: monitor workflow SLA breaches and trigger escalations."""
from __future__ import annotations

import asyncio

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.workflow_sla_monitor_task.check_sla_breaches",
    queue="clm.workflow",
)
def check_sla_breaches() -> dict:
    """Scan active workflow stages for SLA breaches and escalate if needed."""
    return asyncio.run(_async_check())


async def _async_check() -> dict:
    from sqlalchemy import select

    from src.infrastructure.database.models.approval_workflow_model import (
        ApprovalStageModel,
        ApprovalWorkflowModel,
    )
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.workflows.sla_policy import SlaPolicy

    sla = SlaPolicy()
    escalated = 0
    warnings = 0

    async with async_session_factory() as session:
        stmt = (
            select(ApprovalStageModel)
            .join(ApprovalWorkflowModel)
            .where(
                ApprovalStageModel.status == "IN_PROGRESS",
                ApprovalWorkflowModel.status.in_(["PENDING", "IN_PROGRESS"]),
            )
        )
        stages = (await session.scalars(stmt)).all()

        for stage in stages:
            # Build a lightweight entity for SLA check
            from src.domain.entities.approval_stage import ApprovalStage
            from src.domain.value_objects.approval_status import ApprovalStatus

            entity = ApprovalStage(
                id=stage.id,
                workflow_id=stage.workflow_id,
                stage_order=stage.stage_order,
                stage_type=stage.stage_type,
                status=ApprovalStatus.IN_PROGRESS,
                created_at=stage.due_at,  # approximate creation from due_at
            )
            status = sla.check_stage(entity)

            if status == "BREACHED":
                escalated += 1
                log.warning(
                    "sla.escalation_triggered",
                    stage_id=str(stage.id),
                    workflow_id=str(stage.workflow_id),
                )
                # Mark escalation timestamp
                from datetime import UTC, datetime

                stage.escalation_at = datetime.now(UTC)
            elif status == "WARNING":
                warnings += 1

        if escalated > 0:
            await session.commit()

    log.info("sla_monitor.complete", escalated=escalated, warnings=warnings)
    return {"escalated": escalated, "warnings": warnings}
