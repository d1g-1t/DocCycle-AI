"""Obligation policy domain service — deadline and penalty logic."""

from __future__ import annotations

from datetime import UTC, datetime

from src.domain.entities.contract_obligation import ContractObligation
from src.domain.value_objects.obligation_status import ObligationStatus


class ObligationPolicyService:
    """Enforces obligation lifecycle policy rules."""

    @staticmethod
    def mark_overdue(obligations: list[ContractObligation], now: datetime | None = None) -> list[ContractObligation]:
        """Transition open/overdue obligations past their due_date to OVERDUE."""
        now = now or datetime.now(UTC)
        updated: list[ContractObligation] = []
        for ob in obligations:
            if (
                ob.status == ObligationStatus.OPEN
                and ob.due_date is not None
                and ob.due_date < now
            ):
                ob.status = ObligationStatus.OVERDUE
                updated.append(ob)
        return updated
