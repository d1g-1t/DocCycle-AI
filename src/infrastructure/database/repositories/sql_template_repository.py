"""SQLAlchemy template repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.contract_template import ContractTemplate
from src.domain.entities.template_version import TemplateVersion
from src.domain.repositories.i_template_repository import ITemplateRepository
from src.infrastructure.database.models.contract_template_model import (
    ContractTemplateModel,
    TemplateVersionModel,
)


def _tmpl_to_entity(m: ContractTemplateModel) -> ContractTemplate:
    return ContractTemplate(
        id=m.id,
        tenant_id=m.tenant_id,
        name=m.name,
        contract_type=m.contract_type,
        status=m.status,
        current_version_id=m.current_version_id,
        created_by=m.created_by,
        created_at=m.created_at,
    )


def _ver_to_entity(m: TemplateVersionModel) -> TemplateVersion:
    return TemplateVersion(
        id=m.id,
        template_id=m.template_id,
        version_number=m.version_number,
        status=m.status,
        dsl=m.dsl,
        variables=m.variables,
        render_policy=m.render_policy,
        checksum=m.checksum,
        published_at=m.published_at,
        created_by=m.created_by,
        created_at=m.created_at,
    )


class SqlTemplateRepository(ITemplateRepository):
    """Concrete template repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_template_by_id(self, template_id: UUID, tenant_id: UUID) -> ContractTemplate | None:
        stmt = select(ContractTemplateModel).where(
            ContractTemplateModel.id == template_id,
            ContractTemplateModel.tenant_id == tenant_id,
        )
        row = await self._session.scalar(stmt)
        return _tmpl_to_entity(row) if row else None

    async def list_templates(self, tenant_id: UUID, offset: int = 0, limit: int = 50) -> list[ContractTemplate]:
        stmt = (
            select(ContractTemplateModel)
            .where(ContractTemplateModel.tenant_id == tenant_id)
            .order_by(ContractTemplateModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = await self._session.scalars(stmt)
        return [_tmpl_to_entity(r) for r in rows.all()]

    async def save_template(self, template: ContractTemplate) -> ContractTemplate:
        model = ContractTemplateModel(
            id=template.id,
            tenant_id=template.tenant_id,
            name=template.name,
            contract_type=template.contract_type,
            status=template.status,
            current_version_id=template.current_version_id,
            created_by=template.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return template

    async def get_version(self, version_id: UUID) -> TemplateVersion | None:
        stmt = select(TemplateVersionModel).where(TemplateVersionModel.id == version_id)
        row = await self._session.scalar(stmt)
        return _ver_to_entity(row) if row else None

    async def save_version(self, version: TemplateVersion) -> TemplateVersion:
        model = TemplateVersionModel(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            status=version.status,
            dsl=version.dsl,
            variables=version.variables,
            render_policy=version.render_policy,
            checksum=version.checksum,
            published_at=version.published_at,
            created_by=version.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return version

    async def list_versions(self, template_id: UUID) -> list[TemplateVersion]:
        stmt = (
            select(TemplateVersionModel)
            .where(TemplateVersionModel.template_id == template_id)
            .order_by(TemplateVersionModel.version_number.desc())
        )
        rows = await self._session.scalars(stmt)
        return [_ver_to_entity(r) for r in rows.all()]
