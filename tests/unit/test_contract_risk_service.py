"""Unit tests for ContractRiskService."""
from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import UTC, datetime

import pytest

from src.domain.entities.contract import Contract
from src.domain.services.contract_risk_service import ContractRiskService
from src.domain.value_objects.contract_status import ContractStatus
from src.domain.value_objects.contract_type import ContractType
from src.domain.value_objects.risk_level import RiskLevel


def make_contract(amount: Decimal | None = None, counterparty: bool = True) -> Contract:
    now = datetime.now(UTC)
    return Contract(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Test",
        contract_type=ContractType.NDA,
        status=ContractStatus.DRAFT,
        amount=amount,
        currency="USD",
        counterparty_id=uuid.uuid4() if counterparty else None,
        metadata={},
        created_by=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


def test_low_amount_is_low_risk() -> None:
    c = make_contract(amount=Decimal("50000"))
    score = ContractRiskService.compute_base_risk(c)
    assert ContractRiskService.classify(score) == RiskLevel.LOW


def test_critical_amount_raises_score() -> None:
    c = make_contract(amount=Decimal("100_000_000"))
    score = ContractRiskService.compute_base_risk(c)
    assert score >= Decimal("25")


def test_no_counterparty_adds_risk() -> None:
    with_party = make_contract(counterparty=True)
    without_party = make_contract(counterparty=False)
    score_with = ContractRiskService.compute_base_risk(with_party)
    score_without = ContractRiskService.compute_base_risk(without_party)
    assert score_without > score_with


def test_classify_thresholds() -> None:
    assert ContractRiskService.classify(Decimal("10")) == RiskLevel.LOW
    assert ContractRiskService.classify(Decimal("30")) == RiskLevel.MEDIUM
    assert ContractRiskService.classify(Decimal("60")) == RiskLevel.HIGH
    assert ContractRiskService.classify(Decimal("80")) == RiskLevel.CRITICAL
