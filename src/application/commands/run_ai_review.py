from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.review_dto import ReviewResultResponse, RunAiReviewRequest
from src.domain.exceptions import NotFoundError
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository

log = structlog.get_logger(__name__)


class RunAiReviewCommand:
    """Enqueue AI review pipeline — actual work done by Celery worker."""

    def __init__(self, session: AsyncSession) -> None:
        self._contracts = SqlContractRepository(session)

    async def execute(
        self,
        req: RunAiReviewRequest,
        tenant_id: uuid.UUID,
        initiated_by: uuid.UUID,
    ) -> ReviewResultResponse:
        contract = await self._contracts.get_by_id(req.contract_id, tenant_id)
        if contract is None:
            raise NotFoundError("Contract", str(req.contract_id))

        run_id = uuid.uuid4()
        now = datetime.now(UTC)

        from src.infrastructure.queue.tasks.ai_review_task import run_ai_review

        run_ai_review.apply_async(
            kwargs={
                "run_id": str(run_id),
                "contract_id": str(req.contract_id),
                "tenant_id": str(tenant_id),
                "include_clause_suggestions": req.include_clause_suggestions,
                "include_playbook_check": req.include_playbook_check,
            },
            queue="clm.ai",
        )

        log.info("ai_review.enqueued", run_id=str(run_id), contract_id=str(req.contract_id))
        return ReviewResultResponse(
            run_id=run_id,
            contract_id=req.contract_id,
            pipeline_type="contract_review",
            status="pending",
            risk_score=None,
            red_flags=[],
            clause_reviews=[],
            playbook_deviations=[],
            negotiation_summary=None,
            created_at=now,
        )
