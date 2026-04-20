from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RunAiReviewRequest(BaseModel):
    contract_id: UUID
    contract_version_id: UUID | None = None
    include_clause_suggestions: bool = True
    include_playbook_check: bool = True


class ClauseReviewItem(BaseModel):
    clause_text: str
    category: str
    risk_level: str
    issues: list[str]
    suggestion: str | None


class PlaybookDeviationItem(BaseModel):
    rule_name: str
    severity: str
    explanation: str
    fallback_clause_id: UUID | None


class ReviewResultResponse(BaseModel):
    run_id: UUID
    contract_id: UUID
    pipeline_type: str
    status: str
    risk_score: float | None
    red_flags: list[str]
    clause_reviews: list[ClauseReviewItem]
    playbook_deviations: list[PlaybookDeviationItem]
    negotiation_summary: str | None
    created_at: datetime
