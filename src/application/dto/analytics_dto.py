from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class HybridSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    source_types: list[str] = ["CONTRACT", "CLAUSE_LIBRARY"]
    top_k: int = Field(default=10, ge=1, le=50)
    contract_type: str | None = None
    risk_level: str | None = None


class SearchResultItem(BaseModel):
    source_type: str
    source_id: UUID
    chunk_index: int
    content: str
    score: float
    metadata: dict[str, object]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total: int


class CycleTimeResponse(BaseModel):
    avg_draft_to_signed_days: float
    avg_review_days: float
    avg_approval_days: float
    total_contracts: int


class AnalyticsResponse(BaseModel):
    label: str
    value: float | int | str
    metadata: dict[str, object] = Field(default_factory=dict)
