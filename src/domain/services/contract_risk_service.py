from __future__ import annotations

from decimal import Decimal

from src.domain.entities.contract import Contract
from src.domain.value_objects.risk_level import RiskLevel


class ContractRiskService:

    AMOUNT_THRESHOLDS: dict[RiskLevel, Decimal] = {
        RiskLevel.CRITICAL: Decimal("50_000_000"),
        RiskLevel.HIGH: Decimal("10_000_000"),
        RiskLevel.MEDIUM: Decimal("1_000_000"),
    }

    @staticmethod
    def compute_base_risk(contract: Contract) -> Decimal:
        score = Decimal("10")

        if contract.amount:
            for level, threshold in ContractRiskService.AMOUNT_THRESHOLDS.items():
                if contract.amount >= threshold:
                    score += Decimal(str(level_weight(level)))
                    break

        if not contract.counterparty_id:
            score += Decimal("5")

        if contract.jurisdiction and contract.jurisdiction.upper() not in ("RU", "RUSSIA"):
            score += Decimal("10")

        return min(score, Decimal("100"))

    @staticmethod
    def classify(score: Decimal) -> RiskLevel:
        if score >= 75:
            return RiskLevel.CRITICAL
        if score >= 50:
            return RiskLevel.HIGH
        if score >= 25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


def level_weight(level: RiskLevel) -> int:
    return {
        RiskLevel.CRITICAL: 40,
        RiskLevel.HIGH: 25,
        RiskLevel.MEDIUM: 15,
        RiskLevel.LOW: 5,
    }.get(level, 0)
