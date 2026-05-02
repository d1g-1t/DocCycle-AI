"""SQLAlchemy clause library repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.clause_library_entry import ClauseLibraryEntry
from src.domain.repositories.i_clause_library_repository import IClauseLibraryRepository
from src.infrastructure.database.models.clause_library_entry_model import ClauseLibraryEntryModel


def _to_entity(m: ClauseLibraryEntryModel) -> ClauseLibraryEntry:
    return ClauseLibraryEntry(
        id=m.id, tenant_id=m.tenant_id, category=m.category,
        title=m.title, canonical_text=m.canonical_text,
        fallback_text=m.fallback_text, risk_level=m.risk_level,
        tags=m.tags or [], metadata=m.metadata_ or {},
        created_by=m.created_by, created_at=m.created_at,
    )


class SqlClauseLibraryRepository(IClauseLibraryRepository):
    """Concrete clause library repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, clause_id: UUID, tenant_id: UUID) -> ClauseLibraryEntry | None:
        stmt = select(ClauseLibraryEntryModel).where(
            ClauseLibraryEntryModel.id == clause_id,
            ClauseLibraryEntryModel.tenant_id == tenant_id,
        )
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def list_by_category(
        self, tenant_id: UUID, category: str, offset: int = 0, limit: int = 50,
    ) -> list[ClauseLibraryEntry]:
        stmt = (
            select(ClauseLibraryEntryModel)
            .where(
                ClauseLibraryEntryModel.tenant_id == tenant_id,
                ClauseLibraryEntryModel.category == category,
            )
            .order_by(ClauseLibraryEntryModel.created_at.desc())
            .offset(offset).limit(limit)
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def search(self, tenant_id: UUID, query: str) -> list[ClauseLibraryEntry]:
        stmt = (
            select(ClauseLibraryEntryModel)
            .where(
                ClauseLibraryEntryModel.tenant_id == tenant_id,
                ClauseLibraryEntryModel.canonical_text.icontains(query),
            )
            .limit(20)
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def save(self, entry: ClauseLibraryEntry) -> ClauseLibraryEntry:
        model = ClauseLibraryEntryModel(
            id=entry.id, tenant_id=entry.tenant_id, category=entry.category,
            title=entry.title, canonical_text=entry.canonical_text,
            fallback_text=entry.fallback_text, risk_level=entry.risk_level,
            tags=entry.tags, created_by=entry.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return entry
