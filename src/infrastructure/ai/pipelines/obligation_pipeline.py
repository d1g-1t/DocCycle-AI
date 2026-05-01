"""AI pipeline for obligation extraction from contract text."""
from __future__ import annotations

import json
from uuid import UUID, uuid4

import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage
from src.infrastructure.ai.services.prompt_loader import render_prompt

log = structlog.get_logger(__name__)


class ObligationPipeline:
    """Extract structured obligations from contract text via LLM."""

    def __init__(self, llm: ILlmService) -> None:
        self._llm = llm

    async def extract(self, text: str) -> list[dict]:
        """Run obligation extraction on contract text. Returns list of obligation dicts."""
        prompt = render_prompt("obligation_extraction", text=text[:8000])
        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content="You are a legal AI assistant."),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )

        try:
            items = json.loads(resp.content)
            if not isinstance(items, list):
                log.warning("obligation_pipeline.not_list")
                return []
            return items
        except json.JSONDecodeError:
            log.error("obligation_pipeline.parse_error")
            return []
