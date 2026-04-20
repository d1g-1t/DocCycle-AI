from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.start_approval_workflow import workflow_to_response
from src.application.dto.workflow_dto import ApproveStageRequest, RejectStageRequest, WorkflowResponse
from src.domain.entities.approval_decision import ApprovalDecision
from src.domain.exceptions import NotFoundError
from src.domain.value_objects.approval_status import ApprovalStatus
from src.infrastructure.database.repositories.sql_workflow_repository import SqlWorkflowRepository

log = structlog.get_logger(__name__)


class ApproveStageCommand:
    def __init__(self, session: AsyncSession) -> None:
        self._workflows = SqlWorkflowRepository(session)

    async def execute(
        self,
        workflow_id: uuid.UUID,
        stage_id: uuid.UUID,
        req: ApproveStageRequest,
        approver_id: uuid.UUID,
    ) -> WorkflowResponse:
        workflow = await self._workflows.get_workflow_by_id(workflow_id)
        if workflow is None:
            raise NotFoundError("ApprovalWorkflow", str(workflow_id))

        stage = await self._workflows.get_stage_by_id(stage_id)
        if stage is None or stage.workflow_id != workflow_id:
            raise NotFoundError("ApprovalStage", str(stage_id))

        now = datetime.now(UTC)
        stage.status = ApprovalStatus.APPROVED
        await self._workflows.update_stage(stage)

        decision = ApprovalDecision(
            stage_id=stage_id,
            decision="approved",
            comment=req.comment,
            decided_by=approver_id,
            decided_at=now,
        )
        await self._workflows.save_decision(decision)

        all_stages = await self._workflows.list_stages(workflow_id)
        all_approved = all(s.status == ApprovalStatus.APPROVED for s in all_stages)
        if all_approved:
            workflow.status = ApprovalStatus.APPROVED
            workflow.completed_at = now
        await self._workflows.update_workflow(workflow)

        log.info("stage.approved", workflow_id=str(workflow_id), stage_id=str(stage_id))
        return workflow_to_response(workflow, all_stages)


class RejectStageCommand:
    def __init__(self, session: AsyncSession) -> None:
        self._workflows = SqlWorkflowRepository(session)

    async def execute(
        self,
        workflow_id: uuid.UUID,
        stage_id: uuid.UUID,
        req: RejectStageRequest,
        approver_id: uuid.UUID,
    ) -> WorkflowResponse:
        workflow = await self._workflows.get_workflow_by_id(workflow_id)
        if workflow is None:
            raise NotFoundError("ApprovalWorkflow", str(workflow_id))

        stage = await self._workflows.get_stage_by_id(stage_id)
        if stage is None or stage.workflow_id != workflow_id:
            raise NotFoundError("ApprovalStage", str(stage_id))

        now = datetime.now(UTC)
        stage.status = ApprovalStatus.REJECTED
        await self._workflows.update_stage(stage)

        decision = ApprovalDecision(
            stage_id=stage_id,
            decision="rejected",
            comment=req.comment,
            decided_by=approver_id,
            decided_at=now,
        )
        await self._workflows.save_decision(decision)

        workflow.status = ApprovalStatus.REJECTED
        workflow.completed_at = now
        await self._workflows.update_workflow(workflow)

        all_stages = await self._workflows.list_stages(workflow_id)
        log.info("stage.rejected", workflow_id=str(workflow_id), stage_id=str(stage_id))
        return workflow_to_response(workflow, all_stages)
