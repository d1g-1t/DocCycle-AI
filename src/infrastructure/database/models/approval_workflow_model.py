"""Approval workflow, stage, and decision ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base


class ApprovalWorkflowModel(Base):
    __tablename__ = "approval_workflows"
    __table_args__ = (
        Index("idx_approval_workflows_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    route_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]
    sla_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    stages: Mapped[list[ApprovalStageModel]] = relationship(
        "ApprovalStageModel", back_populates="workflow", lazy="selectin", order_by="ApprovalStageModel.stage_order"
    )


class ApprovalStageModel(Base):
    __tablename__ = "approval_stages"
    __table_args__ = (
        Index("idx_approval_stages_due", "status", "due_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("approval_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_type: Mapped[str] = mapped_column(String(64), nullable=False)
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    escalation_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")  # type: ignore[type-arg]

    workflow: Mapped[ApprovalWorkflowModel] = relationship("ApprovalWorkflowModel", back_populates="stages", lazy="noload")
    decisions: Mapped[list[ApprovalDecisionModel]] = relationship("ApprovalDecisionModel", back_populates="stage", lazy="noload")


class ApprovalDecisionModel(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("approval_stages.id", ondelete="CASCADE"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("api_users.id"), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    stage: Mapped[ApprovalStageModel] = relationship("ApprovalStageModel", back_populates="decisions", lazy="noload")
