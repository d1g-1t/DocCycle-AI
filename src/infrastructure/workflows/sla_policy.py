"""SLA policy enforcement for approval workflow stages."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog

from src.domain.entities.approval_stage import ApprovalStage

log = structlog.get_logger(__name__)


class SlaPolicy:
    """Check and enforce SLA deadlines for approval stages."""

    def __init__(self, warning_minutes: int = 60, escalation_minutes: int = 480) -> None:
        self._warning = timedelta(minutes=warning_minutes)
        self._escalation = timedelta(minutes=escalation_minutes)

    def check_stage(self, stage: ApprovalStage) -> str:
        """Return SLA status: 'OK', 'WARNING', 'BREACHED'."""
        if stage.status != "IN_PROGRESS":
            return "OK"

        elapsed = datetime.now(UTC) - (stage.created_at or datetime.now(UTC))
        if elapsed > self._escalation:
            log.warning("sla.breached", stage_id=str(stage.id), elapsed_min=elapsed.total_seconds() / 60)
            return "BREACHED"
        if elapsed > self._warning:
            log.info("sla.warning", stage_id=str(stage.id), elapsed_min=elapsed.total_seconds() / 60)
            return "WARNING"
        return "OK"

    def needs_escalation(self, stage: ApprovalStage) -> bool:
        return self.check_stage(stage) == "BREACHED"
