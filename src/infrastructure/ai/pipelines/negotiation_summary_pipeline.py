"""AI pipeline for negotiation summary generation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import structlog

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage
from src.infrastructure.ai.services.prompt_loader import get_prompt, render_prompt

log = structlog.get_logger(__name__)


@dataclass
class NegotiationChange:
    """Single change between contract versions."""

    section: str
    change_type: str  # added | removed | modified
    original: str
    revised: str
    impact: str  # favorable | neutral | unfavorable
    explanation: str


@dataclass
class NegotiationSummary:
    """Full negotiation summary comparing two versions."""

    changes: list[NegotiationChange] = field(default_factory=list)
    summary: str = ""
    risk_delta: str = "neutral"  # increased | decreased | neutral
    key_concessions: list[str] = field(default_factory=list)
    remaining_concerns: list[str] = field(default_factory=list)


class NegotiationSummaryPipeline:
    """Compare contract versions and generate negotiation summary via LLM."""

    def __init__(self, llm: ILlmService) -> None:
        self._llm = llm

    async def summarize(
        self,
        original_text: str,
        revised_text: str,
    ) -> NegotiationSummary:
        """Generate negotiation summary from two contract versions."""
        prompt = render_prompt(
            "negotiation_summary",
            original_text=original_text[:4000],
            revised_text=revised_text[:4000],
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
            log.warning("negotiation_summary.parse_error")
            return NegotiationSummary(summary="Failed to generate summary.")

        changes = [
            NegotiationChange(
                section=c.get("section", ""),
                change_type=c.get("change_type", "modified"),
                original=c.get("original", ""),
                revised=c.get("revised", ""),
                impact=c.get("impact", "neutral"),
                explanation=c.get("explanation", ""),
            )
            for c in data.get("changes", [])
        ]

        log.info("negotiation_summary.complete", changes=len(changes))
        return NegotiationSummary(
            changes=changes,
            summary=data.get("summary", ""),
            risk_delta=data.get("risk_delta", "neutral"),
            key_concessions=data.get("key_concessions", []),
            remaining_concerns=data.get("remaining_concerns", []),
        )
