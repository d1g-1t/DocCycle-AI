from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Counterparty(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    name: str
    inn: str | None = None
    ogrn: str | None = None
    country_code: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
