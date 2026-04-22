from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.obligation_dto import ObligationDashboardResponse, ObligationResponse
from src.domain.entities.contract_obligation import ContractObligation
from src.infrastructure.database.models.contract_obligation_model import ContractObligationModel
from src.infrastructure.database.repositories.sql_obligation_repository import SqlObligationRepository


def _map(ob: ContractObligation) -> ObligationResponse:
    return ObligationResponse(
        id=ob.id, contract_id=ob.contract_id, title=ob.title,
        description=ob.description, responsible_role=ob.responsible_role,
        responsible_user_id=ob.responsible_user_id, due_date=ob.due_date,
        status=ob.status.value, penalty_text=ob.penalty_text,
        renewal_window_start=ob.renewal_window_start,
        renewal_window_end=ob.renewal_window_end,
        created_at=ob.created_at, completed_at=ob.completed_at,
    )


def _map_from_model(m: ContractObligationModel) -> ObligationResponse:
    return ObligationResponse(
        id=m.id, contract_id=m.contract_id, title=m.title,
        description=m.description, responsible_role=m.responsible_role,
        responsible_user_id=m.responsible_user_id, due_date=m.due_date,
        status=m.status, penalty_text=m.penalty_text,
        renewal_window_start=m.renewal_window_start,
        renewal_window_end=m.renewal_window_end,
        created_at=m.created_at, completed_at=m.completed_at,
    )


class GetObligationsDashboardQuery:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SqlObligationRepository(session)

    async def execute(self, tenant_id: uuid.UUID, days_ahead: int = 30) -> ObligationDashboardResponse:
        upcoming = await self._repo.list_upcoming(tenant_id, days=days_ahead)
        overdue = await self._repo.list_overdue(tenant_id)

        # Renewal window obligations — where current date falls in [renewal_window_start, renewal_window_end]
        now = datetime.now(UTC)
        renewal_stmt = (
            select(ContractObligationModel)
            .where(
                ContractObligationModel.status.in_(["OPEN", "IN_PROGRESS"]),
                ContractObligationModel.renewal_window_start.is_not(None),
                ContractObligationModel.renewal_window_start <= now + timedelta(days=days_ahead),
                ContractObligationModel.renewal_window_end >= now,
            )
            .order_by(ContractObligationModel.renewal_window_start.asc())
            .limit(50)
        )
        renewal_rows = (await self._session.scalars(renewal_stmt)).all()

        return ObligationDashboardResponse(
            upcoming=[_map(o) for o in upcoming],
            overdue=[_map(o) for o in overdue],
            renewals=[_map_from_model(r) for r in renewal_rows],
        )
