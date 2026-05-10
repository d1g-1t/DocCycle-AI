"""Templates router — CRUD and version publishing."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.create_template import CreateTemplateCommand
from src.application.commands.publish_template_version import PublishTemplateVersionCommand
from src.application.dto.template_dto import (
    CreateTemplateRequest,
    CreateTemplateVersionRequest,
    TemplateResponse,
    TemplateVersionResponse,
)
from src.infrastructure.database.session import get_session
from src.presentation.deps import CurrentUserId, TenantId

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    req: CreateTemplateRequest,
    tenant_id: TenantId,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_session),
) -> TemplateResponse:
    return await CreateTemplateCommand(session).execute(req, tenant_id, user_id)


@router.post(
    "/{template_id}/versions",
    response_model=TemplateVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_version(
    template_id: uuid.UUID,
    req: CreateTemplateVersionRequest,
    tenant_id: TenantId,
    user_id: CurrentUserId,
    session: AsyncSession = Depends(get_session),
) -> TemplateVersionResponse:
    return await PublishTemplateVersionCommand(session).execute(
        template_id, tenant_id, req, user_id,
    )
