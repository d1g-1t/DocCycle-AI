"""Contract ORM model — the core aggregate root."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base


class ContractModel(Base):
    """Core contract record — links versions, workflow, obligations."""

    __tablename__ = "contracts"
    __table_args__ = (
        Index("idx_contracts_tenant_status", "tenant_id", "status"),
        Index("idx_contracts_counterparty", "counterparty_id"),
        Index("idx_contracts_metadata_gin", "metadata", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("counterparties.id"), nullable=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contract_templates.id"), nullable=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contract_versions.id", use_alter=True, name="fk_contracts_current_version"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    business_unit: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships — loaded only when explicitly joined (no N+1)
    versions: Mapped[list[ContractVersionModel]] = relationship(
        "ContractVersionModel",
        primaryjoin="ContractModel.id == ContractVersionModel.contract_id",
        back_populates="contract",
        lazy="noload",
    )
    obligations: Mapped[list] = relationship(
        "ContractObligationModel", back_populates="contract", lazy="noload"
    )


class ContractVersionModel(Base):
    """Immutable content snapshot of a contract at a point in time."""

    __tablename__ = "contract_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_text: Mapped[str] = mapped_column(nullable=False)
    rendered_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    redline_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    extracted_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    contract: Mapped[ContractModel] = relationship(
        "ContractModel",
        primaryjoin="ContractVersionModel.contract_id == ContractModel.id",
        back_populates="versions",
        lazy="noload",
    )
