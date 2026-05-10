"""Unit tests for ContractObligation entity."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from src.domain.entities.contract_obligation import ContractObligation
from src.domain.value_objects.obligation_status import ObligationStatus


def test_complete_sets_status():
    ob = ContractObligation(
        contract_id=uuid.uuid4(),
        contract_version_id=uuid.uuid4(),
        title="Pay invoice",
    )
    ob.complete()
    assert ob.status == ObligationStatus.COMPLETED
    assert ob.completed_at is not None


def test_overdue_when_past_due():
    ob = ContractObligation(
        contract_id=uuid.uuid4(),
        contract_version_id=uuid.uuid4(),
        title="Review",
        due_date=datetime.now(UTC) - timedelta(days=1),
        status=ObligationStatus.OPEN,
    )
    assert ob.is_overdue is True


def test_not_overdue_when_future():
    ob = ContractObligation(
        contract_id=uuid.uuid4(),
        contract_version_id=uuid.uuid4(),
        title="Review",
        due_date=datetime.now(UTC) + timedelta(days=30),
        status=ObligationStatus.OPEN,
    )
    assert ob.is_overdue is False


def test_completed_is_not_overdue():
    ob = ContractObligation(
        contract_id=uuid.uuid4(),
        contract_version_id=uuid.uuid4(),
        title="Review",
        due_date=datetime.now(UTC) - timedelta(days=1),
        status=ObligationStatus.COMPLETED,
    )
    assert ob.is_overdue is False
