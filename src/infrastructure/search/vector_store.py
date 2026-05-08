"""pgvector-backed vector store for semantic search."""
from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.i_embedding_service import IEmbeddingService

log = structlog.get_logger(__name__)


class PgVectorStore:
    """Store and query embeddings in PostgreSQL via pgvector extension."""

    def __init__(self, session: AsyncSession, embedder: IEmbeddingService) -> None:
        self._session = session
        self._embedder = embedder

    async def upsert(
        self,
        source_id: UUID,
        source_type: str,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        """Insert or update a single embedding row."""
        await self._session.execute(
            text("""
                INSERT INTO search_embeddings (id, source_type, source_id, chunk_index, content, embedding, metadata)
                VALUES (gen_random_uuid(), :source_type, :source_id, :chunk_index, :content, :embedding, :metadata::jsonb)
                ON CONFLICT (source_id, chunk_index) DO UPDATE
                SET content = EXCLUDED.content, embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
            """),
            {
                "source_type": source_type,
                "source_id": str(source_id),
                "chunk_index": chunk_index,
                "content": content,
                "embedding": str(embedding),
                "metadata": "{}",
            },
        )

    async def similarity_search(
        self,
        query_text: str,
        *,
        top_k: int = 10,
        source_types: list[str] | None = None,
        min_score: float = 0.5,
    ) -> list[dict]:
        """Cosine similarity search against stored embeddings."""
        query_vec = await self._embedder.embed(query_text)
        type_filter = ""
        params: dict = {"embedding": str(query_vec), "top_k": top_k, "min_score": min_score}
        if source_types:
            type_filter = "AND source_type = ANY(:source_types)"
            params["source_types"] = source_types

        rows = await self._session.execute(
            text(f"""
                SELECT id, source_type, source_id, chunk_index, content,
                       1 - (embedding <=> :embedding::vector) AS score
                FROM search_embeddings
                WHERE 1 - (embedding <=> :embedding::vector) >= :min_score
                {type_filter}
                ORDER BY embedding <=> :embedding::vector
                LIMIT :top_k
            """),
            params,
        )
        return [dict(r._mapping) for r in rows.fetchall()]
