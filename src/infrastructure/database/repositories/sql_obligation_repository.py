"""SQLAlchemy obligation repository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.contract_obligation import ContractObligation
from src.domain.repositories.i_obligation_repository import IObligationRepository
from src.domain.value_objects.obligation_status import ObligationStatus
from src.infrastructure.database.models.contract_obligation_model import ContractObligationModel


def _to_entity(m: ContractObligationModel) -> ContractObligation:
    return ContractObligation(
        id=m.id,
        contract_id=m.contract_id,
        contract_version_id=m.contract_version_id,
        title=m.title,
        description=m.description,
        responsible_role=m.responsible_role,
        responsible_user_id=m.responsible_user_id,
        due_date=m.due_date,
        renewal_window_start=m.renewal_window_start,
        renewal_window_end=m.renewal_window_end,
        penalty_text=m.penalty_text,
        status=ObligationStatus(m.status),
        metadata=m.metadata_,
        created_at=m.created_at,
        completed_at=m.completed_at,
    )


class SqlObligationRepository(IObligationRepository):
    """Concrete obligation repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, obligation_id: UUID) -> ContractObligation | None:
        stmt = select(ContractObligationModel).where(ContractObligationModel.id == obligation_id)
        row = await self._session.scalar(stmt)
        return _to_entity(row) if row else None

    async def list_by_contract(self, contract_id: UUID) -> list[ContractObligation]:
        stmt = (
            select(ContractObligationModel)
            .where(ContractObligationModel.contract_id == contract_id)
            .order_by(ContractObligationModel.due_date.asc().nullslast())
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def list_upcoming(self, tenant_id: UUID, days: int = 30, limit: int = 50) -> list[ContractObligation]:
        now = datetime.now(UTC)
        cutoff = now + timedelta(days=days)
        stmt = (
            select(ContractObligationModel)
            .join(ContractObligationModel.contract)  # type: ignore[arg-type]
            .where(
                ContractObligationModel.status.in_(["OPEN", "IN_PROGRESS"]),
                ContractObligationModel.due_date >= now,
                ContractObligationModel.due_date <= cutoff,
            )
            .order_by(ContractObligationModel.due_date.asc())
            .limit(limit)
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def list_overdue(self, tenant_id: UUID, limit: int = 50) -> list[ContractObligation]:
        now = datetime.now(UTC)
        stmt = (
            select(ContractObligationModel)
            .where(
                ContractObligationModel.status.in_(["OPEN", "OVERDUE"]),
                ContractObligationModel.due_date < now,
            )
            .order_by(ContractObligationModel.due_date.asc())
            .limit(limit)
        )
        rows = await self._session.scalars(stmt)
        return [_to_entity(r) for r in rows.all()]

    async def save(self, obligation: ContractObligation) -> ContractObligation:
        model = ContractObligationModel(
            id=obligation.id,
            contract_id=obligation.contract_id,
            contract_version_id=obligation.contract_version_id,
            title=obligation.title,
            description=obligation.description,
            responsible_role=obligation.responsible_role,
            responsible_user_id=obligation.responsible_user_id,
            due_date=obligation.due_date,
            renewal_window_start=obligation.renewal_window_start,
            renewal_window_end=obligation.renewal_window_end,
            penalty_text=obligation.penalty_text,
            status=obligation.status.value,
            metadata_=obligation.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return obligation

    async def update(self, obligation: ContractObligation) -> ContractObligation:
        stmt = select(ContractObligationModel).where(ContractObligationModel.id == obligation.id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ValueError(f"Obligation {obligation.id} not found")
        model.status = obligation.status.value
        model.completed_at = obligation.completed_at
        model.responsible_user_id = obligation.responsible_user_id
        await self._session.flush()
        return obligation

    async def save_many(self, obligations: list[ContractObligation]) -> list[ContractObligation]:
        models = [
            ContractObligationModel(
                id=ob.id,
                contract_id=ob.contract_id,
                contract_version_id=ob.contract_version_id,
                title=ob.title,
                description=ob.description,
                responsible_role=ob.responsible_role,
                due_date=ob.due_date,
                status=ob.status.value,
                metadata_=ob.metadata,
            )
            for ob in obligations
        ]
        self._session.add_all(models)
        await self._session.flush()
        return obligations
