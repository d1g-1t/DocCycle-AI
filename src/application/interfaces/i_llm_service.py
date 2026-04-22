from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LlmMessage:
    role: str
    content: str


@dataclass(slots=True)
class LlmResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    trace_id: str | None = None


class ILlmService(ABC):

    @abstractmethod
    async def chat(
        self,
        messages: list[LlmMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        json_mode: bool = False,
        trace_metadata: dict[str, Any] | None = None,
    ) -> LlmResponse:
        """Send a conversation and return the model completion."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the LLM backend is reachable."""
