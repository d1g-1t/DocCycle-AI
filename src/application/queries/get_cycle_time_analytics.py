from __future__ import annotations

import uuid

from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.analytics_dto import CycleTimeResponse
from src.infrastructure.database.models.approval_workflow_model import ApprovalWorkflowModel
from src.infrastructure.database.models.ai_analysis_run_model import AiAnalysisRunModel
from src.infrastructure.database.models.contract_model import ContractModel


class GetCycleTimeAnalyticsQuery:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, tenant_id: uuid.UUID) -> CycleTimeResponse:
        total = await self._session.scalar(
            select(func.count(ContractModel.id)).where(ContractModel.tenant_id == tenant_id)
        ) or 0

        avg_draft_to_signed_q = (
            select(
                func.avg(
                    extract(
                        "epoch",
                        ContractModel.updated_at - ContractModel.created_at,
                    )
                    / 86400
                )
            )
            .where(
                ContractModel.tenant_id == tenant_id,
                ContractModel.status.in_(["SIGNED", "ACTIVE", "ARCHIVED"]),
            )
        )
        avg_draft_to_signed = await self._session.scalar(avg_draft_to_signed_q) or 0.0

        avg_review_q = (
            select(func.avg(AiAnalysisRunModel.latency_ms / 1000.0 / 86400))
            .where(
                AiAnalysisRunModel.tenant_id == tenant_id,
                AiAnalysisRunModel.status == "SUCCESS",
            )
        )
        avg_review = await self._session.scalar(avg_review_q) or 0.0

        avg_approval_q = (
            select(
                func.avg(
                    extract(
                        "epoch",
                        ApprovalWorkflowModel.completed_at - ApprovalWorkflowModel.started_at,
                    )
                    / 86400
                )
            )
            .where(
                ApprovalWorkflowModel.status.in_(["COMPLETED", "APPROVED"]),
                ApprovalWorkflowModel.completed_at.is_not(None),
            )
        )
        avg_approval = await self._session.scalar(avg_approval_q) or 0.0

        return CycleTimeResponse(
            avg_draft_to_signed_days=round(float(avg_draft_to_signed), 2),
            avg_review_days=round(float(avg_review), 4),
            avg_approval_days=round(float(avg_approval), 2),
            total_contracts=total,
        )
