from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.ai_analysis_run import AiAnalysisRun


class IAiAnalysisRepository(ABC):

    @abstractmethod
    async def get_by_id(self, run_id: UUID) -> AiAnalysisRun | None: ...

    @abstractmethod
    async def get_latest_by_contract(
        self, contract_id: UUID, pipeline_type: str | None = None
    ) -> AiAnalysisRun | None: ...

    @abstractmethod
    async def save(self, run: AiAnalysisRun) -> AiAnalysisRun: ...

    @abstractmethod
    async def list_by_contract(self, contract_id: UUID) -> list[AiAnalysisRun]: ...
