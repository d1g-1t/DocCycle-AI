"""Escalation logic for breached SLA on approval stages."""
from __future__ import annotations

import structlog

from src.domain.entities.approval_stage import ApprovalStage

log = structlog.get_logger(__name__)


class EscalationService:
    """Handle SLA breaches by escalating to next-level approver."""

    @staticmethod
    async def escalate(stage: ApprovalStage, notification_callback=None) -> None:
        """Escalate a stage to the next level."""
        log.warning(
            "escalation.triggered",
            stage_id=str(stage.id),
            approver_id=str(stage.approver_id) if hasattr(stage, 'approver_id') else "unknown",
        )
        if notification_callback:
            await notification_callback(
                subject=f"Approval Stage Escalated: {stage.id}",
                body=f"Stage {stage.id} has breached SLA and requires immediate attention.",
            )
