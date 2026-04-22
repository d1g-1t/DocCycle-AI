from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.playbook_evaluator import PlaybookEvaluator, PlaybookViolation
from src.infrastructure.database.repositories.sql_playbook_repository import SqlPlaybookRepository


class SimulatePlaybookRequest(BaseModel):
    contract_text: str
    contract_type: str
    tenant_id: UUID


class SimulatePlaybookResult(BaseModel):
    violations_count: int
    violations: list[dict]
    passed: bool


class SimulatePlaybookUseCase:

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlPlaybookRepository(session)

    async def execute(self, req: SimulatePlaybookRequest) -> SimulatePlaybookResult:
        rules = await self._repo.list_active_by_type(req.tenant_id, req.contract_type)
        violations = PlaybookEvaluator.evaluate(req.contract_text, rules)

        return SimulatePlaybookResult(
            violations_count=len(violations),
            violations=[
                {
                    "rule_name": v.rule_name,
                    "severity": v.severity,
                    "explanation": v.explanation,
                    "fallback_clause_id": v.fallback_clause_id,
                }
                for v in violations
            ],
            passed=len(violations) == 0,
        )
