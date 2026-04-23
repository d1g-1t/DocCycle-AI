from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.contract_template import ContractTemplate
from src.domain.entities.template_version import TemplateVersion


class ITemplateRepository(ABC):

    @abstractmethod
    async def get_template_by_id(self, template_id: UUID, tenant_id: UUID) -> ContractTemplate | None: ...

    @abstractmethod
    async def list_templates(self, tenant_id: UUID, offset: int = 0, limit: int = 50) -> list[ContractTemplate]: ...

    @abstractmethod
    async def save_template(self, template: ContractTemplate) -> ContractTemplate: ...

    @abstractmethod
    async def get_version(self, version_id: UUID) -> TemplateVersion | None: ...

    @abstractmethod
    async def save_version(self, version: TemplateVersion) -> TemplateVersion: ...

    @abstractmethod
    async def list_versions(self, template_id: UUID) -> list[TemplateVersion]: ...
