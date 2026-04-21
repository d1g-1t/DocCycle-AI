from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import orjson
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.template_dto import CreateTemplateVersionRequest, TemplateVersionResponse
from src.domain.entities.template_version import TemplateVersion
from src.domain.exceptions import NotFoundError
from src.infrastructure.database.repositories.sql_template_repository import SqlTemplateRepository

log = structlog.get_logger(__name__)


class PublishTemplateVersionCommand:

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlTemplateRepository(session)

    async def execute(
        self, template_id: uuid.UUID, tenant_id: uuid.UUID,
        req: CreateTemplateVersionRequest, published_by: uuid.UUID,
    ) -> TemplateVersionResponse:
        template = await self._repo.get_template_by_id(template_id, tenant_id)
        if template is None:
            raise NotFoundError("ContractTemplate", str(template_id))

        existing = await self._repo.list_versions(template_id)
        next_num = max((v.version_number for v in existing), default=0) + 1
        now = datetime.now(UTC)
        dsl_bytes = orjson.dumps(req.dsl, option=orjson.OPT_SORT_KEYS)

        version = TemplateVersion(
            id=uuid.uuid4(),
            template_id=template_id,
            version_number=next_num,
            status="PUBLISHED",
            dsl=req.dsl,
            variables=req.variables,
            render_policy=req.render_policy,
            checksum=hashlib.sha256(dsl_bytes).hexdigest(),
            published_at=now,
            created_by=published_by,
            created_at=now,
        )
        await self._repo.save_version(version)
        log.info("template_version.published", template_id=str(template_id), version=next_num)

        return TemplateVersionResponse(
            id=version.id, template_id=version.template_id,
            version_number=version.version_number, status=version.status,
            dsl=version.dsl, variables=version.variables,
            checksum=version.checksum, published_at=version.published_at,
            created_at=version.created_at,
        )
