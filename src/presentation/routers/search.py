"""Search router — hybrid vector + FTS search."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.analytics_dto import HybridSearchRequest, SearchResponse
from src.application.queries.search_contracts import SearchContractsQuery
from src.infrastructure.database.session import get_session
from src.presentation.deps import TenantId

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    req: HybridSearchRequest,
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    return await SearchContractsQuery(session).execute(req, str(tenant_id))
