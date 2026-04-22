from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.value_objects.obligation_status import ObligationStatus


class ContractObligation(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    contract_version_id: UUID
    title: str
    description: str | None = None
    responsible_role: str | None = None
    responsible_user_id: UUID | None = None
    due_date: datetime | None = None
    renewal_window_start: datetime | None = None
    renewal_window_end: datetime | None = None
    penalty_text: str | None = None
    status: ObligationStatus = ObligationStatus.OPEN
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def complete(self) -> None:
        self.status = ObligationStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        return datetime.now(UTC) > self.due_date and self.status == ObligationStatus.OPEN
