from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.template_dto import CreateTemplateRequest, TemplateResponse
from src.domain.entities.contract_template import ContractTemplate
from src.infrastructure.database.repositories.sql_template_repository import SqlTemplateRepository

log = structlog.get_logger(__name__)


class CreateTemplateCommand:

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlTemplateRepository(session)

    async def execute(
        self, req: CreateTemplateRequest, tenant_id: uuid.UUID, created_by: uuid.UUID,
    ) -> TemplateResponse:
        template = ContractTemplate(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=req.name,
            contract_type=req.contract_type,
            status="DRAFT",
            current_version_id=None,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        await self._repo.save_template(template)
        log.info("template.created", template_id=str(template.id), name=template.name)
        return TemplateResponse(
            id=template.id, tenant_id=template.tenant_id, name=template.name,
            contract_type=template.contract_type, status=template.status,
            current_version_id=template.current_version_id,
            created_at=template.created_at,
        )
