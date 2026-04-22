from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.contract import Contract


class IContractRepository(ABC):

    @abstractmethod
    async def get_by_id(self, contract_id: UUID, tenant_id: UUID) -> Contract | None: ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        status: str | None = None,
        contract_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Contract]: ...

    @abstractmethod
    async def count_by_tenant(
        self,
        tenant_id: UUID,
        *,
        status: str | None = None,
        contract_type: str | None = None,
    ) -> int: ...

    @abstractmethod
    async def save(self, contract: Contract) -> Contract: ...

    @abstractmethod
    async def update(self, contract: Contract) -> Contract: ...

    @abstractmethod
    async def delete(self, contract_id: UUID, tenant_id: UUID) -> None: ...
