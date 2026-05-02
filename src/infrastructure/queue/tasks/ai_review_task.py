"""Celery task: AI contract review."""
from __future__ import annotations

import asyncio

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.ai_review_task.run_ai_review",
    queue="clm.ai",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
)
def run_ai_review(contract_id: str, tenant_id: str, run_id: str) -> dict:
    """Run the AI review pipeline for a contract version."""
    return asyncio.run(_async_review(contract_id, tenant_id, run_id))


async def _async_review(contract_id: str, tenant_id: str, run_id: str) -> dict:
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from src.infrastructure.ai.pipelines.contract_review_pipeline import ContractReviewPipeline
    from src.infrastructure.ai.ollama_llm_service import OllamaLlmService
    from src.infrastructure.database.models.ai_analysis_run_model import AiAnalysisRunModel
    from src.infrastructure.database.models.contract_model import ContractModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.parsing.clause_splitter import extract_text_from_html, split_into_clauses

    cid = UUID(contract_id)
    tid = UUID(tenant_id)
    rid = UUID(run_id)

    async with async_session_factory() as session:
        contract = await session.scalar(
            select(ContractModel).where(ContractModel.id == cid, ContractModel.tenant_id == tid)
        )
        if not contract:
            log.error("ai_review.contract_not_found", contract_id=contract_id)
            return {"status": "FAILED", "error": "contract not found"}

        # Get latest version text
        from src.infrastructure.database.models.contract_model import ContractVersionModel

        version = await session.scalar(
            select(ContractVersionModel)
            .where(ContractVersionModel.contract_id == cid)
            .order_by(ContractVersionModel.version_number.desc())
            .limit(1)
        )
        if not version or not version.content_text:
            log.error("ai_review.no_version_text", contract_id=contract_id)
            return {"status": "FAILED", "error": "no version text"}

        text = extract_text_from_html(version.content_text)
        clauses = split_into_clauses(text)

        llm = OllamaLlmService()
        pipeline = ContractReviewPipeline(llm)
        result = await pipeline.run(
            run_id=rid,
            contract_id=cid,
            contract_html=version.content_text,
            clauses=clauses,
        )

        # Persist AI analysis run
        ai_run = AiAnalysisRunModel(
            id=rid,
            tenant_id=tid,
            contract_id=cid,
            contract_version_id=version.id,
            pipeline_type="contract_review",
            model_name=llm._model,
            prompt_hash="review-v1",
            prompt_version="1.0",
            input_snapshot={"clauses_count": len(clauses)},
            output_snapshot={
                "risk_score": result.risk_score,
                "summary": result.summary,
                "red_flags": result.playbook_deviations,
                "clause_reviews": [
                    {
                        "clause_type": cr.clause_type,
                        "risk_level": cr.risk_level,
                        "issues": cr.issues,
                    }
                    for cr in result.clause_reviews
                ],
            },
            status="SUCCESS",
        )
        session.add(ai_run)

        # Update contract risk_score
        from decimal import Decimal
        contract.risk_score = Decimal(str(result.risk_score))
        await session.commit()

    log.info("ai_review.complete", run_id=run_id, risk_score=result.risk_score)
    return {"status": "SUCCESS", "risk_score": result.risk_score}
