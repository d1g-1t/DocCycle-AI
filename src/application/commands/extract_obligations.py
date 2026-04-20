from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import NotFoundError
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository

log = structlog.get_logger(__name__)


class ExtractObligationsCommand:

    def __init__(self, session: AsyncSession) -> None:
        self._contracts = SqlContractRepository(session)

    async def execute(
        self, contract_id: uuid.UUID, tenant_id: uuid.UUID,
    ) -> dict[str, str]:
        contract = await self._contracts.get_by_id(contract_id, tenant_id)
        if contract is None:
            raise NotFoundError("Contract", str(contract_id))

        from src.infrastructure.queue.tasks.obligation_extraction_task import extract_obligations

        extract_obligations.apply_async(
            kwargs={"contract_id": str(contract_id), "tenant_id": str(tenant_id)},
            queue="clm.ai",
        )
        log.info("obligations.extraction_enqueued", contract_id=str(contract_id))
        return {"status": "enqueued", "contract_id": str(contract_id)}
