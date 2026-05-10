"""Unit tests for RBAC role hierarchy."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from src.core.security import TokenPayload
from src.infrastructure.security.rbac import require_role


def make_token(role: str) -> TokenPayload:
    return TokenPayload(
        sub=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role=role,
        iat=datetime.now(UTC),
        exp=datetime.now(UTC) + timedelta(hours=1),
    )


def test_admin_passes_editor_check():
    check = require_role("editor")
    token = make_token("admin")
    result = check(token)
    assert result.role == "admin"


def test_viewer_fails_editor_check():
    check = require_role("editor")
    token = make_token("viewer")
    with pytest.raises(HTTPException) as exc_info:
        check(token)
    assert exc_info.value.status_code == 403


def test_approver_passes_approver_check():
    check = require_role("approver")
    token = make_token("approver")
    result = check(token)
    assert result.role == "approver"
