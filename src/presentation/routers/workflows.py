"""Approval workflows router."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.approve_reject_stage import ApproveStageCommand, RejectStageCommand
from src.application.commands.start_approval_workflow import StartApprovalWorkflowCommand
from src.application.dto.workflow_dto import (
    ApproveStageRequest,
    RejectStageRequest,
    StartWorkflowRequest,
    WorkflowResponse,
)
from src.infrastructure.database.session import get_session
from src.presentation.deps import CurrentUserId, TenantId

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def start_workflow(
    req: StartWorkflowRequest,
    tenant_id: TenantId,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_session),
) -> WorkflowResponse:
    return await StartApprovalWorkflowCommand(session).execute(req, tenant_id, user_id)


@router.post(
    "/{workflow_id}/stages/{stage_id}/approve",
    response_model=WorkflowResponse,
)
async def approve_stage(
    workflow_id: uuid.UUID,
    stage_id: uuid.UUID,
    req: ApproveStageRequest,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_session),
) -> WorkflowResponse:
    return await ApproveStageCommand(session).execute(workflow_id, stage_id, req, user_id)


@router.post(
    "/{workflow_id}/stages/{stage_id}/reject",
    response_model=WorkflowResponse,
)
async def reject_stage(
    workflow_id: uuid.UUID,
    stage_id: uuid.UUID,
    req: RejectStageRequest,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_session),
) -> WorkflowResponse:
    return await RejectStageCommand(session).execute(workflow_id, stage_id, req, user_id)
