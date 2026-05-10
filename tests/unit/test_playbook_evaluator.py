"""Unit tests for PlaybookEvaluator domain service."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.entities.playbook_rule import PlaybookRule
from src.domain.services.playbook_evaluator import PlaybookEvaluator


def make_keyword_rule(keywords: list[str], rule_type: str = "KEYWORD") -> PlaybookRule:
    return PlaybookRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        contract_type="NDA",
        rule_name="Test Rule",
        severity="MEDIUM",
        rule_type=rule_type,
        condition_json={"keywords": keywords},
        explanation="Test explanation",
        is_active=True,
    )


def make_clause_missing_rule(required_phrases: list[str]) -> PlaybookRule:
    return PlaybookRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        contract_type="NDA",
        rule_name="Clause Missing Rule",
        severity="HIGH",
        rule_type="CLAUSE_MISSING",
        condition_json={"required_phrases": required_phrases},
        explanation="Required clause not found",
        is_active=True,
    )


def test_keyword_present_causes_violation() -> None:
    """KEYWORD rule triggers when ALL keywords are present."""
    rule = make_keyword_rule(["unlimited liability"])
    violations = PlaybookEvaluator.evaluate(
        "Vendor accepts unlimited liability for all damages.", [rule]
    )
    assert len(violations) == 1
    assert violations[0].rule_id == str(rule.id)


def test_keyword_absent_no_violation() -> None:
    rule = make_keyword_rule(["unlimited liability"])
    violations = PlaybookEvaluator.evaluate(
        "Vendor's liability is capped at the contract value.", [rule]
    )
    assert violations == []


def test_clause_missing_triggers_violation() -> None:
    rule = make_clause_missing_rule(["mutual non-disclosure"])
    violations = PlaybookEvaluator.evaluate(
        "The vendor shall keep information confidential.", [rule]
    )
    assert len(violations) == 1


def test_clause_present_no_violation() -> None:
    rule = make_clause_missing_rule(["mutual non-disclosure"])
    violations = PlaybookEvaluator.evaluate(
        "This is a mutual non-disclosure agreement.", [rule]
    )
    assert violations == []


def test_inactive_rule_skipped() -> None:
    rule = make_keyword_rule(["unlimited liability"])
    rule = rule.model_copy(update={"is_active": False})
    violations = PlaybookEvaluator.evaluate(
        "Vendor accepts unlimited liability for all damages.", [rule]
    )
    assert violations == []
