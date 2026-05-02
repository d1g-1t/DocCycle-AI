"""SQLAlchemy AI analysis run repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.ai_analysis_run import AiAnalysisRun
from src.infrastructure.database.models.ai_analysis_run_model import AiAnalysisRunModel


def _to_entity(m: AiAnalysisRunModel) -> AiAnalysisRun:
    return AiAnalysisRun(
        id=m.id, tenant_id=m.tenant_id, contract_id=m.contract_id,
        contract_version_id=m.contract_version_id, pipeline_type=m.pipeline_type,
        model_name=m.model_name, prompt_hash=m.prompt_hash, prompt_version=m.prompt_version,
        input_snapshot=m.input_snapshot, output_snapshot=m.output_snapshot,
        status=m.status, latency_ms=m.latency_ms,
        prompt_tokens=m.prompt_tokens, completion_tokens=m.completion_tokens,
        trace_id=m.trace_id, created_at=m.created_at,
    )


class SqlAiAnalysisRepository:
    """Repository for AI analysis run audit records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, run_id: UUID) -> AiAnalysisRun | None:
        row = await self._session.scalar(
            select(AiAnalysisRunModel).where(AiAnalysisRunModel.id == run_id)
        )
        return _to_entity(row) if row else None

    async def get_latest_for_contract(
        self, contract_id: UUID, tenant_id: UUID, pipeline_type: str = "contract_review",
    ) -> AiAnalysisRun | None:
        row = await self._session.scalar(
            select(AiAnalysisRunModel)
            .where(
                AiAnalysisRunModel.contract_id == contract_id,
                AiAnalysisRunModel.tenant_id == tenant_id,
                AiAnalysisRunModel.pipeline_type == pipeline_type,
            )
            .order_by(AiAnalysisRunModel.created_at.desc())
            .limit(1)
        )
        return _to_entity(row) if row else None

    async def list_by_contract(self, contract_id: UUID) -> list[AiAnalysisRun]:
        rows = await self._session.scalars(
            select(AiAnalysisRunModel)
            .where(AiAnalysisRunModel.contract_id == contract_id)
            .order_by(AiAnalysisRunModel.created_at.desc())
        )
        return [_to_entity(r) for r in rows.all()]

    async def save(self, run: AiAnalysisRun) -> AiAnalysisRun:
        model = AiAnalysisRunModel(
            id=run.id, tenant_id=run.tenant_id, contract_id=run.contract_id,
            contract_version_id=run.contract_version_id, pipeline_type=run.pipeline_type,
            model_name=run.model_name, prompt_hash=run.prompt_hash,
            prompt_version=run.prompt_version, input_snapshot=run.input_snapshot,
            output_snapshot=run.output_snapshot, status=run.status,
            latency_ms=run.latency_ms, prompt_tokens=run.prompt_tokens,
            completion_tokens=run.completion_tokens, trace_id=run.trace_id,
        )
        self._session.add(model)
        await self._session.flush()
        return run
