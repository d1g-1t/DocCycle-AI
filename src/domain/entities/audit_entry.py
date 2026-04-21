from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditEntry(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    actor_user_id: UUID | None = None
    resource_type: str
    resource_id: UUID
    action: str
    payload: dict[str, object] = Field(default_factory=dict)
    trace_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
