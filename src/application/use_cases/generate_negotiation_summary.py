from __future__ import annotations

import json
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.i_llm_service import ILlmService, LlmMessage
from src.domain.exceptions import NotFoundError
from src.infrastructure.database.models.contract_model import ContractVersionModel


class NegotiationChange(BaseModel):
    section: str
    change_type: str
    original: str
    revised: str
    impact: str


class NegotiationSummaryResult(BaseModel):
    version_a_id: UUID
    version_b_id: UUID
    changes: list[NegotiationChange]
    summary: str


class GenerateNegotiationSummaryUseCase:

    def __init__(self, session: AsyncSession, llm: ILlmService) -> None:
        self._session = session
        self._llm = llm

    async def execute(
        self,
        version_a_id: UUID,
        version_b_id: UUID,
    ) -> NegotiationSummaryResult:
        va = await self._session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == version_a_id)
        )
        vb = await self._session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == version_b_id)
        )
        if not va:
            raise NotFoundError("ContractVersion", str(version_a_id))
        if not vb:
            raise NotFoundError("ContractVersion", str(version_b_id))

        from src.infrastructure.ai.services.prompt_loader import render_prompt

        prompt = render_prompt(
            "negotiation_summary",
            original_text=(va.content_text or "")[:4000],
            revised_text=(vb.content_text or "")[:4000],
        )

        resp = await self._llm.chat(
            [
                LlmMessage(role="system", content="You are a legal AI assistant."),
                LlmMessage(role="user", content=prompt),
            ],
            json_mode=True,
            temperature=0.2,
        )

        try:
            data = json.loads(resp.content)
        except json.JSONDecodeError:
            data = {"changes": [], "summary": resp.content[:500]}

        changes = [
            NegotiationChange(**c)
            for c in data.get("changes", [])
            if isinstance(c, dict)
        ]

        return NegotiationSummaryResult(
            version_a_id=version_a_id,
            version_b_id=version_b_id,
            changes=changes,
            summary=data.get("summary", "Summary generation failed."),
        )
