from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.domain.entities.contract_obligation import ContractObligation


class RenewalWindowService:

    @staticmethod
    def compute_window(
        end_date: datetime, days_before: int = 30
    ) -> tuple[datetime, datetime]:
        window_end = end_date
        window_start = end_date - timedelta(days=days_before)
        return window_start, window_end

    @staticmethod
    def is_in_renewal_window(obligation: ContractObligation, now: datetime | None = None) -> bool:
        now = now or datetime.now(UTC)
        if obligation.renewal_window_start and obligation.renewal_window_end:
            return obligation.renewal_window_start <= now <= obligation.renewal_window_end
        return False

    @staticmethod
    def obligations_due_soon(
        obligations: list[ContractObligation], days: int = 30, now: datetime | None = None
    ) -> list[ContractObligation]:
        now = now or datetime.now(UTC)
        cutoff = now + timedelta(days=days)
        return [
            o for o in obligations
            if o.due_date and now <= o.due_date <= cutoff
        ]
