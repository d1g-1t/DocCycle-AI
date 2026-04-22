from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.clause_library_entry import ClauseLibraryEntry


class IClauseLibraryRepository(ABC):

    @abstractmethod
    async def get_by_id(self, clause_id: UUID, tenant_id: UUID) -> ClauseLibraryEntry | None: ...

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: UUID, *, category: str | None = None, offset: int = 0, limit: int = 50
    ) -> list[ClauseLibraryEntry]: ...

    @abstractmethod
    async def save(self, entry: ClauseLibraryEntry) -> ClauseLibraryEntry: ...

    @abstractmethod
    async def search_by_embedding(
        self, tenant_id: UUID, embedding: list[float], top_k: int = 5
    ) -> list[ClauseLibraryEntry]: ...
