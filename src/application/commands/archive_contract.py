from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import NotFoundError
from src.domain.value_objects.contract_status import ContractStatus
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository

log = structlog.get_logger(__name__)


class ArchiveContractCommand:
    def __init__(self, session: AsyncSession) -> None:
        self._contracts = SqlContractRepository(session)

    async def execute(self, contract_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        contract = await self._contracts.get_by_id(contract_id, tenant_id)
        if contract is None:
            raise NotFoundError("Contract", str(contract_id))
        contract.transition_to(ContractStatus.ARCHIVED)
        await self._contracts.update(contract)
        log.info("contract.archived", contract_id=str(contract_id))
