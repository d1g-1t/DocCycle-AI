from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RouteStage:

    stage_order: int
    stage_type: str
    assignee_role: str
    sla_hours: int


class ApprovalRoutingService:

    ROUTING_TABLE: list[dict[str, object]] = [
        {
            "min_amount": Decimal("10_000_000"),
            "stages": [
                RouteStage(1, "LEGAL", "legal_counsel", 24),
                RouteStage(2, "FINANCE", "cfo", 8),
                RouteStage(3, "EXECUTIVE", "ceo", 8),
            ],
        },
        {
            "min_amount": Decimal("1_000_000"),
            "stages": [
                RouteStage(1, "LEGAL", "legal_counsel", 24),
                RouteStage(2, "FINANCE", "finance_manager", 16),
            ],
        },
        {
            "min_amount": Decimal("0"),
            "stages": [
                RouteStage(1, "LEGAL", "legal_counsel", 48),
            ],
        },
    ]

    @classmethod
    def compute_route(
        cls,
        contract_type: str,
        amount: Decimal | None,
    ) -> list[RouteStage]:
        effective_amount = amount or Decimal("0")
        for entry in cls.ROUTING_TABLE:
            min_amount: Decimal = entry["min_amount"]  # type: ignore[assignment]
            if effective_amount >= min_amount:
                stages: list[RouteStage] = entry["stages"]  # type: ignore[assignment]
                return stages
        return [RouteStage(1, "LEGAL", "legal_counsel", 48)]
