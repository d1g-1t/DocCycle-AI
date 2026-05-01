from __future__ import annotations

import json
from dataclasses import dataclass

import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage
from src.infrastructure.ai.services.prompt_loader import get_prompt, render_prompt

log = structlog.get_logger(__name__)


@dataclass
class ClauseClassification:

    category: str
    confidence: float
    subcategory: str | None
    key_entities: list[str]
    summary: str


class ClauseClassifierPipeline:

    def __init__(self, llm: ILlmService) -> None:
        self._llm = llm

    async def classify(self, clause_text: str) -> ClauseClassification:
        prompt = render_prompt("clause_classifier", clause_text=clause_text[:3000])
        system = get_prompt("system")

        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=system),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.1,
        )

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            log.warning("clause_classifier.parse_error", text=clause_text[:100])
            data = {}

        return ClauseClassification(
            category=data.get("category", "OTHER"),
            confidence=float(data.get("confidence", 0.5)),
            subcategory=data.get("subcategory"),
            key_entities=data.get("key_entities", []),
            summary=data.get("summary", ""),
        )

    async def classify_batch(self, clauses: list[str]) -> list[ClauseClassification]:
        results: list[ClauseClassification] = []
        for clause in clauses:
            result = await self.classify(clause)
            results.append(result)
        log.info("clause_classifier.batch_complete", count=len(results))
        return results
