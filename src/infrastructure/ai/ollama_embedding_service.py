from __future__ import annotations

import httpx
import structlog

from src.application.interfaces.i_embedding_service import IEmbeddingService
from src.core.config import get_settings

log = structlog.get_logger(__name__)


class OllamaEmbeddingService(IEmbeddingService):

    def __init__(self) -> None:
        s = get_settings()
        self._base_url = s.ollama_base_url
        self._model = s.ollama_embed_model
        self._dim = 768
        self._timeout = httpx.Timeout(120.0, connect=10.0)

    @property
    def dimension(self) -> int:
        return self._dim

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as c:
            resp = await c.post("/api/embeddings", json={"model": self._model, "prompt": text})
            resp.raise_for_status()
            return resp.json()["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as c:
            for text in texts:
                resp = await c.post("/api/embeddings", json={"model": self._model, "prompt": text})
                resp.raise_for_status()
                results.append(resp.json()["embedding"])
        log.debug("embedding.batch", model=self._model, count=len(texts))
        return results
