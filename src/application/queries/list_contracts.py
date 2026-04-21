from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.create_contract_from_template import contract_to_response
from src.application.dto.contract_dto import ContractListResponse
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository


class ListContractsQuery:

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlContractRepository(session)

    async def execute(
        self,
        tenant_id: uuid.UUID,
        *,
        status: str | None = None,
        contract_type: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ContractListResponse:
        offset = (page - 1) * page_size
        contracts = await self._repo.list_by_tenant(
            tenant_id, status=status, contract_type=contract_type,
            offset=offset, limit=page_size,
        )
        total = await self._repo.count_by_tenant(
            tenant_id, status=status, contract_type=contract_type,
        )
        return ContractListResponse(
            items=[contract_to_response(c) for c in contracts],
            total=total, offset=offset, limit=page_size,
        )
