from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateContractFromTemplateRequest(BaseModel):

    template_version_id: UUID
    title: str = Field(min_length=1, max_length=255)
    counterparty_id: UUID | None = None
    amount: Decimal | None = None
    currency: str | None = Field(default=None, max_length=3)
    business_unit: str | None = None
    jurisdiction: str | None = None
    variables: dict[str, object] = Field(default_factory=dict)


class UploadIncomingContractRequest(BaseModel):

    title: str = Field(min_length=1, max_length=255)
    contract_type: str
    counterparty_id: UUID | None = None
    business_unit: str | None = None
    jurisdiction: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class UpdateContractRequest(BaseModel):

    title: str | None = None
    business_unit: str | None = None
    jurisdiction: str | None = None
    metadata: dict[str, object] | None = None


class ContractResponse(BaseModel):

    id: UUID
    tenant_id: UUID
    title: str
    contract_type: str
    status: str
    business_unit: str | None
    amount: Decimal | None
    currency: str | None
    jurisdiction: str | None
    risk_score: Decimal | None
    counterparty_id: UUID | None
    template_id: UUID | None
    current_version_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ContractListResponse(BaseModel):

    items: list[ContractResponse]
    total: int
    offset: int
    limit: int
