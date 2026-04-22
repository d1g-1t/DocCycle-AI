from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TemplateVersion(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    template_id: UUID
    version_number: int
    status: str = "DRAFT"
    dsl: dict[str, object] = Field(default_factory=dict)
    variables: list[dict[str, object]] = Field(default_factory=list)
    render_policy: dict[str, object] = Field(default_factory=dict)
    checksum: str = ""
    published_at: datetime | None = None
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
