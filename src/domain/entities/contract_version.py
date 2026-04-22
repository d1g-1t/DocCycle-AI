from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContractVersion(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    version_number: int
    source_type: str
    content_text: str
    rendered_file_path: str | None = None
    checksum: str
    redline_summary: dict[str, object] = Field(default_factory=dict)
    extracted_metadata: dict[str, object] = Field(default_factory=dict)
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
