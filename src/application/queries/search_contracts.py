from __future__ import annotations

import hashlib
from uuid import UUID

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.analytics_dto import HybridSearchRequest, SearchResponse, SearchResultItem
from src.infrastructure.database.models.search_embedding_model import SearchEmbeddingModel

log = structlog.get_logger(__name__)


class SearchContractsQuery:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, req: HybridSearchRequest, tenant_id: str) -> SearchResponse:
        from src.infrastructure.ai.ollama_embedding_service import OllamaEmbeddingService

        embedder = OllamaEmbeddingService()
        try:
            query_vector = await embedder.embed(req.query)
        except Exception as exc:
            log.warning("search.embedding_failed", error=str(exc))
            return await self._fts_fallback(req, tenant_id)

        vector_literal = f"[{','.join(str(v) for v in query_vector)}]"
        stmt = (
            select(
                SearchEmbeddingModel.source_type,
                SearchEmbeddingModel.source_id,
                SearchEmbeddingModel.chunk_index,
                SearchEmbeddingModel.content,
                SearchEmbeddingModel.metadata_,
                (1 - SearchEmbeddingModel.embedding.cosine_distance(query_vector)).label("score"),
            )
            .where(SearchEmbeddingModel.tenant_id == UUID(tenant_id))
            .where(SearchEmbeddingModel.source_type.in_(req.source_types))
            .order_by(text("score DESC"))
            .limit(req.top_k)
        )

        rows = (await self._session.execute(stmt)).all()

        results = [
            SearchResultItem(
                source_type=r.source_type,
                source_id=r.source_id,
                chunk_index=r.chunk_index,
                content=r.content[:500],
                score=round(float(r.score), 4),
                metadata=r.metadata_ or {},
            )
            for r in rows
            if float(r.score) >= 0.3
        ]

        log.info("search.hybrid", query=req.query[:50], results=len(results))
        return SearchResponse(query=req.query, results=results, total=len(results))

    async def _fts_fallback(self, req: HybridSearchRequest, tenant_id: str) -> SearchResponse:
        stmt = (
            select(
                SearchEmbeddingModel.source_type,
                SearchEmbeddingModel.source_id,
                SearchEmbeddingModel.chunk_index,
                SearchEmbeddingModel.content,
                SearchEmbeddingModel.metadata_,
            )
            .where(
                SearchEmbeddingModel.tenant_id == UUID(tenant_id),
                SearchEmbeddingModel.source_type.in_(req.source_types),
                func.to_tsvector("russian", SearchEmbeddingModel.content).match(req.query),
            )
            .limit(req.top_k)
        )
        rows = (await self._session.execute(stmt)).all()
        results = [
            SearchResultItem(
                source_type=r.source_type,
                source_id=r.source_id,
                chunk_index=r.chunk_index,
                content=r.content[:500],
                score=0.5,
                metadata=r.metadata_ or {},
            )
            for r in rows
        ]
        return SearchResponse(query=req.query, results=results, total=len(results))
