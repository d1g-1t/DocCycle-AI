"""Unit tests for Contract domain entity status transitions."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.entities.contract import Contract
from src.domain.value_objects.contract_status import ContractStatus
from src.domain.value_objects.contract_type import ContractType


def make_contract(status: ContractStatus = ContractStatus.DRAFT) -> Contract:
    now = datetime.now(UTC)
    return Contract(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        title="Test Contract",
        contract_type=ContractType.NDA,
        status=status,
        current_version_id=None,
        template_id=None,
        counterparty_id=None,
        amount=None,
        currency="USD",
        risk_score=None,
        metadata={},
        created_by=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


def test_draft_to_in_review_allowed() -> None:
    c = make_contract(ContractStatus.DRAFT)
    c.transition_to(ContractStatus.IN_REVIEW)
    assert c.status == ContractStatus.IN_REVIEW


def test_draft_to_executed_disallowed() -> None:
    c = make_contract(ContractStatus.DRAFT)
    with pytest.raises(ValueError):
        c.transition_to(ContractStatus.EXECUTED)


def test_in_review_to_in_approval_allowed() -> None:
    c = make_contract(ContractStatus.IN_REVIEW)
    c.transition_to(ContractStatus.IN_APPROVAL)
    assert c.status == ContractStatus.IN_APPROVAL


def test_in_approval_to_approved_allowed() -> None:
    c = make_contract(ContractStatus.IN_APPROVAL)
    c.transition_to(ContractStatus.APPROVED)
    assert c.status == ContractStatus.APPROVED


def test_approved_to_executed_allowed() -> None:
    c = make_contract(ContractStatus.APPROVED)
    c.transition_to(ContractStatus.EXECUTED)
    assert c.status == ContractStatus.EXECUTED


def test_archived_to_any_disallowed() -> None:
    c = make_contract(ContractStatus.ARCHIVED)
    with pytest.raises(ValueError):
        c.transition_to(ContractStatus.DRAFT)
