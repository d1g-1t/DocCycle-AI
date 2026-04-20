from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StartWorkflowRequest(BaseModel):
    contract_id: UUID


class ApproveStageRequest(BaseModel):
    comment: str | None = None


class RejectStageRequest(BaseModel):
    comment: str = Field(min_length=1)
    reason_code: str


class DelegateStageRequest(BaseModel):
    new_assignee_user_id: UUID
    comment: str | None = None


class WorkflowStageResponse(BaseModel):
    id: UUID
    stage_order: int
    stage_type: str
    assignee_user_id: UUID | None
    status: str
    due_at: datetime | None
    escalation_at: datetime | None


class WorkflowResponse(BaseModel):
    id: UUID
    contract_id: UUID
    status: str
    current_stage_order: int
    stages: list[WorkflowStageResponse]
    started_at: datetime
    completed_at: datetime | None
