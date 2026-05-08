"""Hybrid search: combine vector similarity with PostgreSQL full-text search."""
from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.i_embedding_service import IEmbeddingService
from src.infrastructure.search.vector_store import PgVectorStore

log = structlog.get_logger(__name__)


class HybridSearchEngine:
    """Combine pgvector cosine similarity with pg_trgm full-text search."""

    def __init__(self, session: AsyncSession, embedder: IEmbeddingService) -> None:
        self._session = session
        self._vector = PgVectorStore(session, embedder)
        self._embedder = embedder

    async def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        source_types: list[str] | None = None,
        vector_weight: float = 0.7,
        fts_weight: float = 0.3,
    ) -> list[dict]:
        """Execute hybrid search and return ranked results."""
        # Vector results
        vector_results = await self._vector.similarity_search(
            query, top_k=top_k * 2, source_types=source_types,
        )

        # FTS results via pg_trgm
        fts_results = await self._fts_search(query, top_k=top_k * 2, source_types=source_types)

        # Merge by source_id+chunk_index with weighted scoring
        merged: dict[str, dict] = {}
        for r in vector_results:
            key = f"{r['source_id']}:{r['chunk_index']}"
            merged[key] = {**r, "combined_score": float(r["score"]) * vector_weight}

        for r in fts_results:
            key = f"{r['source_id']}:{r['chunk_index']}"
            if key in merged:
                merged[key]["combined_score"] += float(r["fts_score"]) * fts_weight
            else:
                merged[key] = {**r, "combined_score": float(r["fts_score"]) * fts_weight}

        ranked = sorted(merged.values(), key=lambda x: x["combined_score"], reverse=True)
        return ranked[:top_k]

    async def _fts_search(
        self,
        query: str,
        *,
        top_k: int = 20,
        source_types: list[str] | None = None,
    ) -> list[dict]:
        type_filter = ""
        params: dict = {"query": query, "top_k": top_k}
        if source_types:
            type_filter = "AND source_type = ANY(:source_types)"
            params["source_types"] = source_types

        rows = await self._session.execute(
            text(f"""
                SELECT id, source_type, source_id, chunk_index, content,
                       similarity(content, :query) AS fts_score
                FROM search_embeddings
                WHERE similarity(content, :query) > 0.1
                {type_filter}
                ORDER BY fts_score DESC
                LIMIT :top_k
            """),
            params,
        )
        return [dict(r._mapping) for r in rows.fetchall()]
