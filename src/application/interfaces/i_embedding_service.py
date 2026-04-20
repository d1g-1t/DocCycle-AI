from __future__ import annotations

from abc import ABC, abstractmethod


class IEmbeddingService(ABC):

    @abstractmethod
    async def embed(self, text: str) -> list[float]:

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:

    @property
    @abstractmethod
    def dimension(self) -> int:
