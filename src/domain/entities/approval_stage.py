from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.value_objects.approval_status import ApprovalStatus


class ApprovalStage(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    workflow_id: UUID
    stage_order: int
    stage_type: str
    assignee_user_id: UUID | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    due_at: datetime | None = None
    escalation_at: datetime | None = None
    decided_at: datetime | None = None
    created_at: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
