"""Review router — AI review triggers and results."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.run_ai_review import RunAiReviewCommand
from src.application.dto.review_dto import ReviewResultResponse, RunAiReviewRequest
from src.application.queries.get_review_result import GetReviewResultQuery
from src.infrastructure.database.session import get_session
from src.presentation.deps import CurrentUserId, TenantId

router = APIRouter(prefix="/review", tags=["review"])


@router.post(
    "/contracts/{contract_id}/run",
    response_model=ReviewResultResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_review(
    contract_id: uuid.UUID,
    tenant_id: TenantId,
    user_id: CurrentUserId,
    include_clause_suggestions: bool = True,
    include_playbook_check: bool = True,
    session: AsyncSession = Depends(get_session),
) -> ReviewResultResponse:
    req = RunAiReviewRequest(
        contract_id=contract_id,
        include_clause_suggestions=include_clause_suggestions,
        include_playbook_check=include_playbook_check,
    )
    return await RunAiReviewCommand(session).execute(req, tenant_id, user_id)


@router.get("/contracts/{contract_id}/latest", response_model=ReviewResultResponse)
async def get_latest_review(
    contract_id: uuid.UUID,
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> ReviewResultResponse:
    return await GetReviewResultQuery(session).execute(contract_id, tenant_id)
