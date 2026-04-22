from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.value_objects.clause_category import ClauseCategory
from src.domain.value_objects.risk_level import RiskLevel


class ClauseLibraryEntry(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    category: ClauseCategory
    title: str
    canonical_text: str
    fallback_text: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
