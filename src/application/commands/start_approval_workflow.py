from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.workflow_dto import StartWorkflowRequest, WorkflowResponse, WorkflowStageResponse
from src.domain.entities.approval_stage import ApprovalStage
from src.domain.entities.approval_workflow import ApprovalWorkflow
from src.domain.exceptions import NotFoundError
from src.domain.services.approval_routing_service import ApprovalRoutingService
from src.domain.value_objects.approval_status import ApprovalStatus
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository
from src.infrastructure.database.repositories.sql_workflow_repository import SqlWorkflowRepository

log = structlog.get_logger(__name__)


class StartApprovalWorkflowCommand:

    def __init__(self, session: AsyncSession) -> None:
        self._contracts = SqlContractRepository(session)
        self._workflows = SqlWorkflowRepository(session)

    async def execute(
        self,
        req: StartWorkflowRequest,
        tenant_id: uuid.UUID,
        initiated_by: uuid.UUID,
    ) -> WorkflowResponse:
        contract = await self._contracts.get_by_id(req.contract_id, tenant_id)
        if contract is None:
            raise NotFoundError("Contract", str(req.contract_id))

        route = ApprovalRoutingService.compute_route(
            contract.contract_type.value, contract.amount,
        )
        now = datetime.now(UTC)
        workflow_id = uuid.uuid4()
        route_snapshot = [
            {"stage_order": r.stage_order, "stage_type": r.stage_type,
             "assignee_role": r.assignee_role, "sla_hours": r.sla_hours}
            for r in route
        ]

        workflow = ApprovalWorkflow(
            id=workflow_id,
            contract_id=req.contract_id,
            status=ApprovalStatus.IN_PROGRESS,
            current_stage_order=1,
            route_snapshot={"stages": route_snapshot},
            sla_policy={"default_hours": 24},
            started_at=now,
        )
        await self._workflows.save_workflow(workflow)

        stages: list[ApprovalStage] = []
        for rs in route:
            stage = ApprovalStage(
                id=uuid.uuid4(),
                workflow_id=workflow_id,
                stage_order=rs.stage_order,
                stage_type=rs.stage_type,
                status=ApprovalStatus.PENDING,
                due_at=now + timedelta(hours=rs.sla_hours),
            )
            await self._workflows.save_stage(stage)
            stages.append(stage)

        from src.domain.value_objects.contract_status import ContractStatus

        contract.transition_to(ContractStatus.IN_APPROVAL)
        await self._contracts.update(contract)

        log.info("workflow.started", workflow_id=str(workflow_id), stages=len(stages))
        return workflow_to_response(workflow, stages)


def workflow_to_response(
    w: ApprovalWorkflow, stages: list[ApprovalStage] | None = None,
) -> WorkflowResponse:
    stage_responses = [
        WorkflowStageResponse(
            id=s.id, stage_order=s.stage_order, stage_type=s.stage_type,
            assignee_user_id=s.assignee_user_id, status=s.status.value,
            due_at=s.due_at, escalation_at=s.escalation_at,
        )
        for s in (stages or [])
    ]
    return WorkflowResponse(
        id=w.id, contract_id=w.contract_id, status=w.status.value,
        current_stage_order=w.current_stage_order, stages=stage_responses,
        started_at=w.started_at, completed_at=w.completed_at,
    )
