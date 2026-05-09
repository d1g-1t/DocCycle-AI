"""Analytics router — cycle-time, bottlenecks, AI quality."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.analytics_dto import CycleTimeResponse
from src.application.queries.get_cycle_time_analytics import GetCycleTimeAnalyticsQuery
from src.infrastructure.database.session import get_session
from src.presentation.deps import TenantId

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/cycle-time", response_model=CycleTimeResponse)
async def cycle_time(
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> CycleTimeResponse:
    return await GetCycleTimeAnalyticsQuery(session).execute(tenant_id)
