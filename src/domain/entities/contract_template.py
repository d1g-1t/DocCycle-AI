from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContractTemplate(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    contract_type: str
    status: str = "DRAFT"
    current_version_id: UUID | None = None
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
