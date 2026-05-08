"""Celery task: generate negotiation summary between contract versions."""
from __future__ import annotations

import asyncio

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.negotiation_summary_task.run_negotiation_summary",
    queue="clm.ai",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
)
def run_negotiation_summary(
    contract_id: str, from_version_id: str, to_version_id: str, tenant_id: str
) -> dict:
    """Compare two contract versions and generate negotiation summary."""
    return asyncio.run(
        _async_summarize(contract_id, from_version_id, to_version_id, tenant_id)
    )


async def _async_summarize(
    contract_id: str, from_version_id: str, to_version_id: str, tenant_id: str
) -> dict:
    import json
    from uuid import UUID, uuid4

    from sqlalchemy import select

    from src.infrastructure.ai.ollama_llm_service import OllamaLlmService
    from src.infrastructure.ai.pipelines.negotiation_summary_pipeline import (
        NegotiationSummaryPipeline,
    )
    from src.infrastructure.database.models.contract_model import ContractVersionModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.parsing.clause_splitter import extract_text_from_html

    fid = UUID(from_version_id)
    tid = UUID(to_version_id)

    async with async_session_factory() as session:
        from_v = await session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == fid)
        )
        to_v = await session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == tid)
        )

        if not from_v or not to_v:
            return {"status": "FAILED", "reason": "version not found"}

        original = extract_text_from_html(from_v.content_text or "")
        revised = extract_text_from_html(to_v.content_text or "")

        llm = OllamaLlmService()
        pipeline = NegotiationSummaryPipeline(llm)
        result = await pipeline.summarize(original, revised)

        # Store in negotiation_rounds (if table exists)
        log.info(
            "negotiation_summary.complete",
            contract_id=contract_id,
            changes=len(result.changes),
            risk_delta=result.risk_delta,
        )

        return {
            "status": "SUCCESS",
            "summary": result.summary,
            "changes_count": len(result.changes),
            "risk_delta": result.risk_delta,
        }
