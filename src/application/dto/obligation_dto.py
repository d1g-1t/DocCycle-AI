from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompleteObligationRequest(BaseModel):
    comment: str | None = None
    completed_at: datetime | None = None


class ObligationResponse(BaseModel):
    id: UUID
    contract_id: UUID
    title: str
    description: str | None
    responsible_role: str | None
    responsible_user_id: UUID | None
    due_date: datetime | None
    status: str
    penalty_text: str | None
    renewal_window_start: datetime | None
    renewal_window_end: datetime | None
    created_at: datetime
    completed_at: datetime | None


class ObligationDashboardResponse(BaseModel):
    upcoming: list[ObligationResponse]
    overdue: list[ObligationResponse]
    renewals: list[ObligationResponse]
