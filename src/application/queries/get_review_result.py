from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.review_dto import ReviewResultResponse
from src.domain.exceptions import NotFoundError
from src.infrastructure.database.models.ai_analysis_run_model import AiAnalysisRunModel


class GetReviewResultQuery:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, contract_id: uuid.UUID, tenant_id: uuid.UUID) -> ReviewResultResponse:
        stmt = (
            select(AiAnalysisRunModel)
            .where(
                AiAnalysisRunModel.contract_id == contract_id,
                AiAnalysisRunModel.tenant_id == tenant_id,
                AiAnalysisRunModel.pipeline_type == "contract_review",
            )
            .order_by(AiAnalysisRunModel.created_at.desc())
            .limit(1)
        )
        row = await self._session.scalar(stmt)
        if row is None:
            raise NotFoundError("AiAnalysisRun", str(contract_id))

        output = row.output_snapshot or {}
        return ReviewResultResponse(
            run_id=row.id,
            contract_id=row.contract_id or contract_id,
            pipeline_type=row.pipeline_type,
            status=row.status,
            risk_score=output.get("risk_score"),
            red_flags=output.get("red_flags", []),
            clause_reviews=[],
            playbook_deviations=[],
            negotiation_summary=output.get("summary"),
            created_at=row.created_at,
        )
