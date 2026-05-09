"""Approval workflow engine — orchestrates multi-stage approval flows."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog

from src.domain.entities.approval_decision import ApprovalDecision
from src.domain.entities.approval_stage import ApprovalStage
from src.domain.entities.approval_workflow import ApprovalWorkflow
from src.domain.value_objects.approval_action import ApprovalAction

log = structlog.get_logger(__name__)


class WorkflowEngine:
    """Advances an approval workflow through its stages."""

    @staticmethod
    async def advance(
        workflow: ApprovalWorkflow,
        stages: list[ApprovalStage],
        decision: ApprovalDecision,
    ) -> ApprovalWorkflow:
        """Process a decision and potentially advance to next stage."""
        current_stage = next(
            (s for s in stages if s.stage_order == workflow.current_stage_order),
            None,
        )
        if current_stage is None:
            raise ValueError("No current stage found for workflow")

        if decision.action == ApprovalAction.APPROVE:
            current_stage.status = "APPROVED"
            current_stage.decided_at = datetime.now(UTC)

            # Find next pending stage
            remaining = [
                s for s in stages
                if s.stage_order > current_stage.stage_order and s.status == "PENDING"
            ]
            if remaining:
                next_stage = min(remaining, key=lambda s: s.stage_order)
                workflow.current_stage_order = next_stage.stage_order
                next_stage.status = "IN_PROGRESS"
                log.info("workflow.advanced", workflow_id=str(workflow.id), next_stage=str(next_stage.id))
            else:
                workflow.status = "COMPLETED"
                workflow.completed_at = datetime.now(UTC)
                log.info("workflow.completed", workflow_id=str(workflow.id))

        elif decision.action == ApprovalAction.REJECT:
            current_stage.status = "REJECTED"
            current_stage.decided_at = datetime.now(UTC)
            workflow.status = "REJECTED"
            workflow.completed_at = datetime.now(UTC)
            log.info("workflow.rejected", workflow_id=str(workflow.id))

        elif decision.action == ApprovalAction.RETURN_FOR_REVISION:
            current_stage.status = "RETURNED"
            current_stage.decided_at = datetime.now(UTC)
            workflow.status = "RETURNED"
            log.info("workflow.returned", workflow_id=str(workflow.id))

        return workflow
