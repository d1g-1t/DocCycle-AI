"""Unit tests for SLA policy enforcement."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from src.domain.entities.approval_stage import ApprovalStage
from src.domain.value_objects.approval_status import ApprovalStatus
from src.infrastructure.workflows.sla_policy import SlaPolicy


def make_stage(status: str = "IN_PROGRESS", hours_ago: float = 0) -> ApprovalStage:
    return ApprovalStage(
        workflow_id=uuid.uuid4(),
        stage_order=1,
        stage_type="LEGAL",
        status=ApprovalStatus(status),
        created_at=datetime.now(UTC) - timedelta(hours=hours_ago),
    )


def test_ok_within_warning():
    sla = SlaPolicy(warning_minutes=60, escalation_minutes=480)
    stage = make_stage(hours_ago=0.5)
    assert sla.check_stage(stage) == "OK"


def test_warning_after_threshold():
    sla = SlaPolicy(warning_minutes=60, escalation_minutes=480)
    stage = make_stage(hours_ago=2)
    assert sla.check_stage(stage) == "WARNING"


def test_breached_after_escalation():
    sla = SlaPolicy(warning_minutes=60, escalation_minutes=480)
    stage = make_stage(hours_ago=10)
    assert sla.check_stage(stage) == "BREACHED"


def test_non_active_stage_always_ok():
    sla = SlaPolicy(warning_minutes=60, escalation_minutes=480)
    stage = make_stage(status="APPROVED", hours_ago=100)
    assert sla.check_stage(stage) == "OK"
