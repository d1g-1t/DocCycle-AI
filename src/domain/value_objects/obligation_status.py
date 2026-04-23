from __future__ import annotations

from enum import StrEnum


class ObligationStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    WAIVED = "WAIVED"
