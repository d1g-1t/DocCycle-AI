from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage, LlmResponse
from src.core.config import get_settings

log = structlog.get_logger(__name__)


class OllamaLlmService(ILlmService):

    def __init__(self) -> None:
        s = get_settings()
        self._base_url = s.ollama_base_url
        self._model = s.ollama_chat_model
        self._timeout = httpx.Timeout(300.0, connect=10.0)

    async def chat(
        self,
        messages: list[LlmMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        json_mode: bool = False,
        trace_metadata: dict[str, Any] | None = None,
    ) -> LlmResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"

        t0 = time.monotonic()
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.monotonic() - t0) * 1000
        content = data["message"]["content"]
        prompt_eval = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        log.debug(
            "llm.chat",
            model=self._model,
            prompt_tokens=prompt_eval,
            completion_tokens=eval_count,
            latency_ms=round(latency_ms),
        )
        return LlmResponse(
            content=content,
            model=self._model,
            prompt_tokens=prompt_eval,
            completion_tokens=eval_count,
            latency_ms=latency_ms,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=httpx.Timeout(5.0)) as c:
                r = await c.get("/api/tags")
                return r.status_code == 200
        except Exception:  # noqa: BLE001
            return False
