"""SQLAlchemy workflow repository — eager loads stages via selectin."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.approval_decision import ApprovalDecision
from src.domain.entities.approval_stage import ApprovalStage
from src.domain.entities.approval_workflow import ApprovalWorkflow
from src.domain.repositories.i_workflow_repository import IWorkflowRepository
from src.domain.value_objects.approval_status import ApprovalStatus
from src.infrastructure.database.models.approval_workflow_model import (
    ApprovalDecisionModel,
    ApprovalStageModel,
    ApprovalWorkflowModel,
)


def _wf_to_entity(m: ApprovalWorkflowModel) -> ApprovalWorkflow:
    return ApprovalWorkflow(
        id=m.id,
        contract_id=m.contract_id,
        status=ApprovalStatus(m.status),
        current_stage_order=m.current_stage_order,
        route_snapshot=m.route_snapshot,
        sla_policy=m.sla_policy,
        started_at=m.started_at,
        completed_at=m.completed_at,
    )


def _stage_to_entity(m: ApprovalStageModel) -> ApprovalStage:
    return ApprovalStage(
        id=m.id,
        workflow_id=m.workflow_id,
        stage_order=m.stage_order,
        stage_type=m.stage_type,
        assignee_user_id=m.assignee_user_id,
        status=ApprovalStatus(m.status),
        due_at=m.due_at,
        escalation_at=m.escalation_at,
        metadata=m.metadata_,
    )


class SqlWorkflowRepository(IWorkflowRepository):
    """Concrete workflow repository — selectinload prevents N+1 on stages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_workflow_by_id(self, workflow_id: UUID) -> ApprovalWorkflow | None:
        stmt = (
            select(ApprovalWorkflowModel)
            .where(ApprovalWorkflowModel.id == workflow_id)
            .options(selectinload(ApprovalWorkflowModel.stages))
        )
        row = await self._session.scalar(stmt)
        return _wf_to_entity(row) if row else None

    async def get_workflow_by_contract(self, contract_id: UUID) -> ApprovalWorkflow | None:
        stmt = (
            select(ApprovalWorkflowModel)
            .where(ApprovalWorkflowModel.contract_id == contract_id)
            .options(selectinload(ApprovalWorkflowModel.stages))
            .order_by(ApprovalWorkflowModel.started_at.desc())
            .limit(1)
        )
        row = await self._session.scalar(stmt)
        return _wf_to_entity(row) if row else None

    async def save_workflow(self, workflow: ApprovalWorkflow) -> ApprovalWorkflow:
        model = ApprovalWorkflowModel(
            id=workflow.id,
            contract_id=workflow.contract_id,
            status=workflow.status.value,
            current_stage_order=workflow.current_stage_order,
            route_snapshot=workflow.route_snapshot,
            sla_policy=workflow.sla_policy,
            started_at=workflow.started_at,
        )
        self._session.add(model)
        await self._session.flush()
        return workflow

    async def update_workflow(self, workflow: ApprovalWorkflow) -> ApprovalWorkflow:
        stmt = select(ApprovalWorkflowModel).where(ApprovalWorkflowModel.id == workflow.id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ValueError(f"Workflow {workflow.id} not found")
        model.status = workflow.status.value
        model.current_stage_order = workflow.current_stage_order
        model.completed_at = workflow.completed_at
        await self._session.flush()
        return workflow

    async def list_stages(self, workflow_id: UUID) -> list[ApprovalStage]:
        stmt = (
            select(ApprovalStageModel)
            .where(ApprovalStageModel.workflow_id == workflow_id)
            .order_by(ApprovalStageModel.stage_order)
        )
        rows = await self._session.scalars(stmt)
        return [_stage_to_entity(r) for r in rows.all()]

    async def get_stage_by_id(self, stage_id: UUID) -> ApprovalStage | None:
        stmt = select(ApprovalStageModel).where(ApprovalStageModel.id == stage_id)
        row = await self._session.scalar(stmt)
        return _stage_to_entity(row) if row else None

    async def save_stage(self, stage: ApprovalStage) -> ApprovalStage:
        model = ApprovalStageModel(
            id=stage.id,
            workflow_id=stage.workflow_id,
            stage_order=stage.stage_order,
            stage_type=stage.stage_type,
            assignee_user_id=stage.assignee_user_id,
            status=stage.status.value,
            due_at=stage.due_at,
            escalation_at=stage.escalation_at,
            metadata_=stage.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return stage

    async def update_stage(self, stage: ApprovalStage) -> ApprovalStage:
        stmt = select(ApprovalStageModel).where(ApprovalStageModel.id == stage.id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ValueError(f"Stage {stage.id} not found")
        model.status = stage.status.value
        model.assignee_user_id = stage.assignee_user_id
        await self._session.flush()
        return stage

    async def save_decision(self, decision: ApprovalDecision) -> ApprovalDecision:
        model = ApprovalDecisionModel(
            id=decision.id,
            stage_id=decision.stage_id,
            decision=decision.decision,
            comment=decision.comment,
            decided_by=decision.decided_by,
            decided_at=decision.decided_at,
        )
        self._session.add(model)
        await self._session.flush()
        return decision

    async def list_pending_workflows(self, offset: int = 0, limit: int = 50) -> list[ApprovalWorkflow]:
        stmt = (
            select(ApprovalWorkflowModel)
            .where(ApprovalWorkflowModel.status == "IN_PROGRESS")
            .order_by(ApprovalWorkflowModel.started_at)
            .offset(offset)
            .limit(limit)
        )
        rows = await self._session.scalars(stmt)
        return [_wf_to_entity(r) for r in rows.all()]
