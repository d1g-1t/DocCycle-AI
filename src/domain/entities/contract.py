from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.domain.value_objects.contract_status import ContractStatus
from src.domain.value_objects.contract_type import ContractType


class Contract(BaseModel):

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    counterparty_id: UUID | None = None
    template_id: UUID | None = None
    current_version_id: UUID | None = None
    title: str
    contract_type: ContractType
    status: ContractStatus = ContractStatus.DRAFT
    business_unit: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    jurisdiction: str | None = None
    risk_score: Decimal | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def transition_to(self, new_status: ContractStatus) -> None:
        """Validate and apply a status transition."""
        allowed: dict[ContractStatus, set[ContractStatus]] = {
            ContractStatus.DRAFT: {ContractStatus.IN_REVIEW, ContractStatus.ARCHIVED},
            ContractStatus.IN_REVIEW: {ContractStatus.IN_APPROVAL, ContractStatus.DRAFT},
            ContractStatus.IN_APPROVAL: {
                ContractStatus.APPROVED,
                ContractStatus.DRAFT,
                ContractStatus.IN_REVIEW,
            },
            ContractStatus.APPROVED: {ContractStatus.EXECUTED, ContractStatus.ARCHIVED},
            ContractStatus.EXECUTED: {ContractStatus.EXPIRED, ContractStatus.TERMINATED},
            ContractStatus.EXPIRED: {ContractStatus.ARCHIVED},
            ContractStatus.TERMINATED: {ContractStatus.ARCHIVED},
        }
        if new_status not in allowed.get(self.status, set()):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.now(UTC)
