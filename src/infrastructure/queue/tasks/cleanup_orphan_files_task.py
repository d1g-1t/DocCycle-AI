"""Celery beat task: clean up orphaned files in MinIO storage."""
from __future__ import annotations

import asyncio

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.cleanup_orphan_files_task.cleanup_orphan_files",
    queue="clm.maintenance",
)
def cleanup_orphan_files() -> dict:
    """Remove files from MinIO that are no longer referenced by any contract."""
    return asyncio.run(_async_cleanup())


async def _async_cleanup() -> dict:
    from sqlalchemy import select

    from src.infrastructure.database.models.contract_attachment_model import ContractAttachmentModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.storage.minio_storage import MinioFileStorage

    storage = MinioFileStorage()

    async with async_session_factory() as session:
        # Get all referenced paths from the database
        stmt = select(ContractAttachmentModel.storage_path)
        rows = (await session.scalars(stmt)).all()
        referenced_paths = set(rows)

    # List all files in storage
    stored_files = await storage.list_files()
    orphans = [f for f in stored_files if f not in referenced_paths]

    removed = 0
    for orphan_path in orphans:
        try:
            await storage.delete(orphan_path)
            removed += 1
        except Exception as exc:
            log.warning("cleanup.delete_failed", path=orphan_path, error=str(exc))

    log.info("cleanup.complete", total_stored=len(stored_files), removed=removed)
    return {"total_stored": len(stored_files), "orphans_found": len(orphans), "removed": removed}
