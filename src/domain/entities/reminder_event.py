from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReminderEvent(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    obligation_id: UUID
    reminder_type: str
    scheduled_for: datetime
    sent_at: datetime | None = None
    status: str = "PENDING"
    metadata: dict[str, object] = Field(default_factory=dict)
