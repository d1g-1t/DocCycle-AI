from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ApprovalDecision(BaseModel):
    """Record of a human decision on an approval stage."""

    id: UUID = Field(default_factory=uuid4)
    stage_id: UUID
    decision: str  # APPROVED | REJECTED
    comment: str | None = None
    decided_by: UUID
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
