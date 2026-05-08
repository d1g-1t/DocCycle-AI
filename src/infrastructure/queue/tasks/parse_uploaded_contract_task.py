"""Celery task: parse uploaded contract (extract text from PDF/DOCX)."""
from __future__ import annotations

import asyncio
import hashlib

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.parse_uploaded_contract_task.parse_uploaded_contract",
    queue="clm.parse",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def parse_uploaded_contract(
    contract_id: str, version_id: str, file_path: str, tenant_id: str
) -> dict:
    """Extract text from uploaded contract file and store as version content."""
    return asyncio.run(
        _async_parse(contract_id, version_id, file_path, tenant_id)
    )


async def _async_parse(
    contract_id: str, version_id: str, file_path: str, tenant_id: str
) -> dict:
    from uuid import UUID

    from sqlalchemy import select

    from src.infrastructure.database.models.contract_model import ContractVersionModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.parsing.file_extractor import extract_text
    from src.infrastructure.storage.minio_storage import MinioFileStorage

    vid = UUID(version_id)

    # Download file from MinIO
    storage = MinioFileStorage()
    file_bytes = await storage.download(file_path)
    if not file_bytes:
        log.error("parse.file_not_found", path=file_path)
        return {"status": "FAILED", "reason": "file not found"}

    # Extract text
    extension = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else "txt"
    text = extract_text(file_bytes, extension)
    if not text.strip():
        log.warning("parse.empty_text", path=file_path)
        return {"status": "SKIPPED", "reason": "empty text extraction"}

    checksum = hashlib.sha256(text.encode()).hexdigest()

    async with async_session_factory() as session:
        version = await session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == vid)
        )
        if version:
            version.content_text = text
            version.checksum = checksum
            await session.commit()

    log.info(
        "parse.complete",
        contract_id=contract_id,
        version_id=version_id,
        text_length=len(text),
    )
    return {"status": "SUCCESS", "text_length": len(text), "checksum": checksum}
