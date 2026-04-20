from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contract_type: str


class CreateTemplateVersionRequest(BaseModel):
    dsl: dict[str, object] = Field(default_factory=dict)
    variables: list[dict[str, object]] = Field(default_factory=list)
    render_policy: dict[str, object] = Field(default_factory=dict)


class TemplateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    contract_type: str
    status: str
    current_version_id: UUID | None
    created_at: datetime


class TemplateVersionResponse(BaseModel):
    id: UUID
    template_id: UUID
    version_number: int
    status: str
    dsl: dict[str, object]
    variables: list[dict[str, object]]
    checksum: str
    published_at: datetime | None
    created_at: datetime


class TemplatePreviewRequest(BaseModel):
    variables: dict[str, object] = Field(default_factory=dict)
    format: str = "html"  # html | docx
