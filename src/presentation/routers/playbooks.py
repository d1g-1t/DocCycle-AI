"""Playbooks router — CRUD, activation, simulation."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_session
from src.presentation.deps import TenantId

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


class PlaybookResponse(BaseModel):
    id: uuid.UUID
    rule_name: str
    contract_type: str
    severity: str
    is_active: bool


class CreatePlaybookRequest(BaseModel):
    contract_type: str
    rule_name: str
    severity: str
    rule_type: str
    condition_json: dict
    explanation: str


class SimulatePlaybookRequest(BaseModel):
    contract_text: str
    contract_type: str


class SimulatePlaybookResponse(BaseModel):
    violations: list[dict]


@router.get("", response_model=list[PlaybookResponse])
async def list_playbooks(
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> list[PlaybookResponse]:
    from src.infrastructure.database.repositories.sql_playbook_repository import SqlPlaybookRepository
    repo = SqlPlaybookRepository(session)
    rules = await repo.list_by_tenant(tenant_id)
    return [
        PlaybookResponse(
            id=r.id, rule_name=r.rule_name, contract_type=r.contract_type,
            severity=r.severity, is_active=r.is_active,
        )
        for r in rules
    ]


@router.post("/simulate", response_model=SimulatePlaybookResponse)
async def simulate_playbook(
    req: SimulatePlaybookRequest,
    tenant_id: TenantId,
    session: AsyncSession = Depends(get_session),
) -> SimulatePlaybookResponse:
    from src.infrastructure.database.repositories.sql_playbook_repository import SqlPlaybookRepository
    from src.domain.services.playbook_evaluator import PlaybookEvaluator

    repo = SqlPlaybookRepository(session)
    rules = await repo.list_active_by_type(tenant_id, req.contract_type)
    violations = PlaybookEvaluator.evaluate(req.contract_text, rules)
    return SimulatePlaybookResponse(
        violations=[
            {"rule_name": v.rule_name, "severity": v.severity, "explanation": v.explanation}
            for v in violations
        ]
    )
