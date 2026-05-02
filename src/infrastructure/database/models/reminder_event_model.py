"""Reminder event ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base


class ReminderEventModel(Base):
    __tablename__ = "reminder_events"
    __table_args__ = (
        Index("idx_reminders_scheduled", "status", "scheduled_for"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    obligation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contract_obligations.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]

    obligation: Mapped[object] = relationship("ContractObligationModel", back_populates="reminders", lazy="noload")
