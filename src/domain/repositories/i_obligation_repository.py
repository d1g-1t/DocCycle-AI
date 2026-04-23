from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.contract_obligation import ContractObligation


class IObligationRepository(ABC):

    @abstractmethod
    async def get_by_id(self, obligation_id: UUID) -> ContractObligation | None: ...

    @abstractmethod
    async def list_by_contract(self, contract_id: UUID) -> list[ContractObligation]: ...

    @abstractmethod
    async def list_upcoming(self, tenant_id: UUID, days: int = 30, limit: int = 50) -> list[ContractObligation]: ...

    @abstractmethod
    async def list_overdue(self, tenant_id: UUID, limit: int = 50) -> list[ContractObligation]: ...

    @abstractmethod
    async def save(self, obligation: ContractObligation) -> ContractObligation: ...

    @abstractmethod
    async def update(self, obligation: ContractObligation) -> ContractObligation: ...

    @abstractmethod
    async def save_many(self, obligations: list[ContractObligation]) -> list[ContractObligation]: ...
