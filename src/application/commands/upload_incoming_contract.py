from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.create_contract_from_template import contract_to_response
from src.application.dto.contract_dto import ContractResponse, UploadIncomingContractRequest
from src.application.interfaces.i_file_storage import IFileStorage
from src.domain.entities.contract import Contract
from src.domain.entities.contract_version import ContractVersion
from src.domain.value_objects.contract_status import ContractStatus
from src.domain.value_objects.contract_type import ContractType
from src.infrastructure.database.models.contract_model import ContractVersionModel
from src.infrastructure.database.repositories.sql_contract_repository import SqlContractRepository

log = structlog.get_logger(__name__)


class UploadIncomingContractCommand:

    def __init__(self, session: AsyncSession, storage: IFileStorage) -> None:
        self._contracts = SqlContractRepository(session)
        self._storage = storage
        self._session = session

    async def execute(
        self,
        req: UploadIncomingContractRequest,
        file_data: bytes,
        filename: str,
        content_type: str,
        tenant_id: uuid.UUID,
        created_by: uuid.UUID,
    ) -> ContractResponse:
        contract_id = uuid.uuid4()
        version_id = uuid.uuid4()
        now = datetime.now(UTC)

        object_key = f"{tenant_id}/{contract_id}/v1/{filename}"
        uploaded = await self._storage.upload(
            "contractforge-files", object_key, file_data, content_type=content_type,
        )

        contract = Contract(
            id=contract_id,
            tenant_id=tenant_id,
            title=req.title,
            contract_type=ContractType(req.contract_type) if req.contract_type else ContractType.OTHER,
            status=ContractStatus.DRAFT,
            current_version_id=version_id,
            counterparty_id=req.counterparty_id,
            metadata={"original_filename": filename, "object_key": object_key},
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        cv = ContractVersion(
            id=version_id, contract_id=contract_id, version_number=1,
            source_type="UPLOAD", content_text="",  # parsed later by worker
            checksum=hashlib.sha256(file_data).hexdigest(),
            redline_summary={"source": "upload", "filename": filename},
            created_by=created_by, created_at=now,
        )
        await self._contracts.save(contract)
        self._session.add(ContractVersionModel(
            id=cv.id, contract_id=cv.contract_id, version_number=cv.version_number,
            source_type=cv.source_type, content_text=cv.content_text,
            checksum=cv.checksum, redline_summary=cv.redline_summary,
            created_by=cv.created_by, created_at=cv.created_at,
        ))
        await self._session.flush()
        log.info("contract.uploaded", contract_id=str(contract_id), filename=filename)
        return contract_to_response(contract)
