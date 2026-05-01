from __future__ import annotations

import json
from dataclasses import dataclass

import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage
from src.infrastructure.ai.services.prompt_loader import get_prompt, render_prompt

log = structlog.get_logger(__name__)


@dataclass
class ClauseSuggestion:

    original_intent: str
    risk_issues: list[str]
    suggested_clause: str
    explanation: str
    risk_reduction: str


class ClauseSuggestionPipeline:

    def __init__(self, llm: ILlmService) -> None:
        self._llm = llm

    async def suggest(
        self,
        clause_text: str,
        category: str = "OTHER",
        context: str = "",
    ) -> ClauseSuggestion:
        """Generate an improved version of a problematic clause."""
        prompt = render_prompt(
            "clause_suggestion",
            clause_text=clause_text[:3000],
            category=category,
            context=context[:2000],
        )
        system = get_prompt("system")

        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content=system),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.2,
        )

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            log.warning("clause_suggestion.parse_error")
            data = {}

        return ClauseSuggestion(
            original_intent=data.get("original_intent", ""),
            risk_issues=data.get("risk_issues", []),
            suggested_clause=data.get("suggested_clause", clause_text),
            explanation=data.get("explanation", ""),
            risk_reduction=data.get("risk_reduction", "low"),
        )
