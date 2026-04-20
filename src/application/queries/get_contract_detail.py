from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.create_contract_from_template import contract_to_response
from src.application.dto.contract_dto import ContractResponse
from src.domain.exceptions import NotFoundError
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository


class GetContractDetailQuery:

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlContractRepository(session)

    async def execute(self, contract_id: uuid.UUID, tenant_id: uuid.UUID) -> ContractResponse:
        contract = await self._repo.get_by_id(contract_id, tenant_id)
        if contract is None:
            raise NotFoundError("Contract", str(contract_id))
        return contract_to_response(contract)
