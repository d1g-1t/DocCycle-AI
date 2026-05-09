"""File upload router (incoming contracts)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.commands.upload_incoming_contract import UploadIncomingContractCommand
from src.application.dto.contract_dto import ContractResponse, UploadIncomingContractRequest
from src.infrastructure.database.session import get_session
from src.infrastructure.storage.minio_storage import MinioFileStorage
from src.presentation.deps import CurrentUserId, TenantId

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    title: str = Form(...),
    contract_type: str | None = Form(None),
    counterparty_id: str | None = Form(None),
    tenant_id: TenantId = Depends(),
    user_id: CurrentUserId = Depends(),
    session: AsyncSession = Depends(get_session),
) -> ContractResponse:
    data = await file.read()
    from uuid import UUID
    req = UploadIncomingContractRequest(
        title=title,
        contract_type=contract_type or "OTHER",
        counterparty_id=UUID(counterparty_id) if counterparty_id else None,
    )
    storage = MinioFileStorage()
    return await UploadIncomingContractCommand(session, storage).execute(
        req, file_data=data, filename=file.filename or "upload.pdf",
        content_type=file.content_type or "application/octet-stream",
        tenant_id=tenant_id, created_by=user_id,
    )
