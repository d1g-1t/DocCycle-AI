from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.playbook_rule import PlaybookRule


class IPlaybookRepository(ABC):

    @abstractmethod
    async def get_by_id(self, rule_id: UUID, tenant_id: UUID) -> PlaybookRule | None: ...

    @abstractmethod
    async def list_active_by_type(self, tenant_id: UUID, contract_type: str) -> list[PlaybookRule]: ...

    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID, offset: int = 0, limit: int = 50) -> list[PlaybookRule]: ...

    @abstractmethod
    async def save(self, rule: PlaybookRule) -> PlaybookRule: ...

    @abstractmethod
    async def update(self, rule: PlaybookRule) -> PlaybookRule: ...
