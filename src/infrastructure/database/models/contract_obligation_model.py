"""Contract obligation ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base


class ContractObligationModel(Base):
    __tablename__ = "contract_obligations"
    __table_args__ = (
        Index("idx_obligations_due", "status", "due_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contract_versions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    renewal_window_start: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    renewal_window_end: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    penalty_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    contract: Mapped[object] = relationship("ContractModel", back_populates="obligations", lazy="noload")
    reminders: Mapped[list] = relationship("ReminderEventModel", back_populates="obligation", lazy="noload")
