from __future__ import annotations

from enum import StrEnum


class ApprovalAction(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_FOR_REVISION = "RETURN_FOR_REVISION"
    DELEGATE = "DELEGATE"
    ESCALATE = "ESCALATE"
