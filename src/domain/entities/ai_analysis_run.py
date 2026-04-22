from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AiAnalysisRun(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    contract_id: UUID | None = None
    contract_version_id: UUID | None = None
    pipeline_type: str
    model_name: str
    prompt_hash: str
    prompt_version: str
    input_snapshot: dict[str, object] = Field(default_factory=dict)
    output_snapshot: dict[str, object] = Field(default_factory=dict)
    status: str = "PENDING"
    latency_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    trace_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
