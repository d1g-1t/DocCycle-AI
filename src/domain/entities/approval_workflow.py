from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.value_objects.approval_status import ApprovalStatus


class ApprovalWorkflow(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    status: ApprovalStatus = ApprovalStatus.PENDING
    current_stage_order: int = 1
    route_snapshot: dict[str, object] = Field(default_factory=dict)
    sla_policy: dict[str, object] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
