"""Contract template and related ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base


class ContractTemplateModel(Base):
    """Versioned contract template definition."""

    __tablename__ = "contract_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("template_versions.id", use_alter=True, name="fk_contract_templates_current_version"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    versions: Mapped[list[TemplateVersionModel]] = relationship(
        "TemplateVersionModel",
        primaryjoin="ContractTemplateModel.id == TemplateVersionModel.template_id",
        back_populates="template",
        lazy="selectin",
    )


class TemplateVersionModel(Base):
    """Immutable snapshot of a template DSL."""

    __tablename__ = "template_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contract_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    dsl: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]
    variables: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")  # type: ignore[type-arg]
    render_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    template: Mapped[ContractTemplateModel] = relationship(
        "ContractTemplateModel",
        primaryjoin="TemplateVersionModel.template_id == ContractTemplateModel.id",
        back_populates="versions",
        lazy="noload",
    )
