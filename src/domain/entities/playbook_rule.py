from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PlaybookRule(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    contract_type: str
    rule_name: str
    severity: str
    rule_type: str
    condition_json: dict[str, object] = Field(default_factory=dict)
    explanation: str = ""
    fallback_clause_id: UUID | None = None
    is_active: bool = True
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
