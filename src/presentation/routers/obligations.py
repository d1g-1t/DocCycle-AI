"""Obligations router — dashboard, CRUD, completion."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.obligation_dto import (
    CompleteObligationRequest,
    ObligationDashboardResponse,
    ObligationResponse,
)
from src.application.queries.get_obligations_dashboard import GetObligationsDashboardQuery
from src.domain.exceptions import NotFoundError
from src.infrastructure.database.repositories.sql_obligation_repository import SqlObligationRepository
from src.infrastructure.database.session import get_session
from src.presentation.deps import TenantId

router = APIRouter(prefix="/obligations", tags=["obligations"])


@router.get("/dashboard/upcoming", response_model=ObligationDashboardResponse)
async def upcoming_dashboard(
    tenant_id: TenantId,
    days_ahead: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> ObligationDashboardResponse:
    return await GetObligationsDashboardQuery(session).execute(tenant_id, days_ahead=days_ahead)


@router.get("/dashboard/overdue", response_model=ObligationDashboardResponse)
async def overdue_dashboard(
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> ObligationDashboardResponse:
    return await GetObligationsDashboardQuery(session).execute(tenant_id, days_ahead=0)


@router.post("/{obligation_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_obligation(
    obligation_id: uuid.UUID,
    req: CompleteObligationRequest,
    session: AsyncSession = Depends(get_session),
) -> None:
    repo = SqlObligationRepository(session)
    ob = await repo.get_by_id(obligation_id)
    if ob is None:
        raise NotFoundError("ContractObligation", str(obligation_id))
    ob.complete()
    await repo.update(ob)
