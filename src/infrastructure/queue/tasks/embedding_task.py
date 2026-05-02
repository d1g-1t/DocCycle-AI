"""Celery task: compute and store vector embeddings for a contract version."""
from __future__ import annotations

import asyncio
import hashlib

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.embedding_task.compute_embeddings",
    queue="clm.analytics",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
)
def compute_embeddings(contract_id: str, version_id: str, tenant_id: str) -> dict:
    """Chunk a contract version and store vector embeddings in pgvector."""
    return asyncio.run(_async_embed(contract_id, version_id, tenant_id))


async def _async_embed(contract_id: str, version_id: str, tenant_id: str) -> dict:
    from uuid import UUID, uuid4

    from sqlalchemy import select

    from src.infrastructure.ai.ollama_embedding_service import OllamaEmbeddingService
    from src.infrastructure.database.models.contract_model import ContractVersionModel
    from src.infrastructure.database.models.search_embedding_model import SearchEmbeddingModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.parsing.clause_splitter import extract_text_from_html, split_into_clauses

    vid = UUID(version_id)
    cid = UUID(contract_id)
    tid = UUID(tenant_id)

    async with async_session_factory() as session:
        version = await session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == vid)
        )
        if not version or not version.content_text:
            log.warning("embedding.no_text", version_id=version_id)
            return {"status": "SKIPPED", "reason": "no content_text"}

        text = extract_text_from_html(version.content_text)
        chunks = split_into_clauses(text, max_length=1500)

        embedder = OllamaEmbeddingService()
        vectors = await embedder.embed_batch(chunks)

        # Store each chunk + embedding in pgvector search_embeddings table
        stored = 0
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            content_hash = hashlib.sha256(chunk.encode()).hexdigest()

            # Skip if already exists (idempotent)
            existing = await session.scalar(
                select(SearchEmbeddingModel.id).where(
                    SearchEmbeddingModel.content_hash == content_hash
                )
            )
            if existing:
                continue

            embedding_model = SearchEmbeddingModel(
                id=uuid4(),
                tenant_id=tid,
                source_type="CONTRACT",
                source_id=cid,
                chunk_index=idx,
                content=chunk,
                content_hash=content_hash,
                metadata_={
                    "contract_id": str(cid),
                    "version_id": str(vid),
                    "chunk_length": len(chunk),
                },
                embedding=vector,
            )
            session.add(embedding_model)
            stored += 1

        await session.commit()

        log.info(
            "embedding.complete",
            contract_id=contract_id,
            version_id=version_id,
            chunks=len(chunks),
            stored=stored,
            dim=embedder.dimension,
        )
        return {"status": "SUCCESS", "chunks": len(chunks), "stored": stored}
