"""Contracts router — CRUD, review trigger, archival."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.archive_contract import ArchiveContractCommand
from src.application.commands.create_contract_from_template import CreateContractFromTemplateCommand
from src.application.commands.run_ai_review import RunAiReviewCommand
from src.application.dto.contract_dto import (
    ContractListResponse,
    ContractResponse,
    CreateContractFromTemplateRequest,
    UpdateContractRequest,
)
from src.application.dto.review_dto import ReviewResultResponse, RunAiReviewRequest
from src.application.queries.get_contract_detail import GetContractDetailQuery
from src.application.queries.list_contracts import ListContractsQuery
from src.infrastructure.database.session import get_session
from src.infrastructure.templates.jinja2_renderer import Jinja2TemplateRenderer
from src.presentation.deps import CurrentUserId, TenantId

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    tenant_id: TenantId,
    status_filter: str | None = Query(None, alias="status"),
    contract_type: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ContractListResponse:
    return await ListContractsQuery(session).execute(
        tenant_id, status=status_filter, contract_type=contract_type,
        search=search, page=page, page_size=page_size,
    )


@router.post("/from-template", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_from_template(
    req: CreateContractFromTemplateRequest,
    tenant_id: TenantId,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_session),
) -> ContractResponse:
    renderer = Jinja2TemplateRenderer(session)
    return await CreateContractFromTemplateCommand(session, renderer).execute(req, tenant_id, user_id)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: uuid.UUID,
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> ContractResponse:
    return await GetContractDetailQuery(session).execute(contract_id, tenant_id)


@router.post("/{contract_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_contract(
    contract_id: uuid.UUID,
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> None:
    await ArchiveContractCommand(session).execute(contract_id, tenant_id)
