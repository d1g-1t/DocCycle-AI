"""SQLAlchemy contract repository — selectin eager loading, no N+1."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.contract import Contract
from src.domain.entities.contract_version import ContractVersion
from src.domain.repositories.i_contract_repository import IContractRepository
from src.domain.value_objects.contract_status import ContractStatus
from src.domain.value_objects.contract_type import ContractType
from src.infrastructure.database.models.contract_model import ContractModel, ContractVersionModel


def _model_to_entity(m: ContractModel) -> Contract:
    return Contract(
        id=m.id,
        tenant_id=m.tenant_id,
        counterparty_id=m.counterparty_id,
        template_id=m.template_id,
        current_version_id=m.current_version_id,
        title=m.title,
        contract_type=ContractType(m.contract_type),
        status=ContractStatus(m.status),
        business_unit=m.business_unit,
        amount=m.amount,
        currency=m.currency,
        jurisdiction=m.jurisdiction,
        risk_score=m.risk_score,
        metadata=m.metadata_,
        created_by=m.created_by,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SqlContractRepository(IContractRepository):
    """Concrete contract repository using async SQLAlchemy 2."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, contract_id: UUID, tenant_id: UUID) -> Contract | None:
        stmt = select(ContractModel).where(
            ContractModel.id == contract_id,
            ContractModel.tenant_id == tenant_id,
        )
        row = await self._session.scalar(stmt)
        return _model_to_entity(row) if row else None

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        status: str | None = None,
        contract_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Contract]:
        stmt = select(ContractModel).where(ContractModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(ContractModel.status == status)
        if contract_type:
            stmt = stmt.where(ContractModel.contract_type == contract_type)
        stmt = stmt.order_by(ContractModel.created_at.desc()).offset(offset).limit(limit)
        rows = await self._session.scalars(stmt)
        return [_model_to_entity(r) for r in rows.all()]

    async def count_by_tenant(
        self,
        tenant_id: UUID,
        *,
        status: str | None = None,
        contract_type: str | None = None,
    ) -> int:
        stmt = select(func.count(ContractModel.id)).where(ContractModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(ContractModel.status == status)
        if contract_type:
            stmt = stmt.where(ContractModel.contract_type == contract_type)
        result = await self._session.scalar(stmt)
        return result or 0

    async def save(self, contract: Contract) -> Contract:
        model = ContractModel(
            id=contract.id,
            tenant_id=contract.tenant_id,
            counterparty_id=contract.counterparty_id,
            template_id=contract.template_id,
            current_version_id=contract.current_version_id,
            title=contract.title,
            contract_type=contract.contract_type.value,
            status=contract.status.value,
            business_unit=contract.business_unit,
            amount=contract.amount,
            currency=contract.currency,
            jurisdiction=contract.jurisdiction,
            risk_score=contract.risk_score,
            metadata_=contract.metadata,
            created_by=contract.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return contract

    async def update(self, contract: Contract) -> Contract:
        stmt = select(ContractModel).where(ContractModel.id == contract.id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ValueError(f"Contract {contract.id} not found for update")
        model.status = contract.status.value
        model.title = contract.title
        model.current_version_id = contract.current_version_id
        model.risk_score = contract.risk_score
        model.metadata_ = contract.metadata
        model.business_unit = contract.business_unit
        model.amount = contract.amount
        model.currency = contract.currency
        model.jurisdiction = contract.jurisdiction
        await self._session.flush()
        return contract

    async def delete(self, contract_id: UUID, tenant_id: UUID) -> None:
        stmt = select(ContractModel).where(
            ContractModel.id == contract_id,
            ContractModel.tenant_id == tenant_id,
        )
        model = await self._session.scalar(stmt)
        if model:
            await self._session.delete(model)
            await self._session.flush()
