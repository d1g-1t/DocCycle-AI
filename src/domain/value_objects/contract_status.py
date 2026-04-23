from __future__ import annotations

from enum import StrEnum


class ContractStatus(StrEnum):

    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    IN_APPROVAL = "IN_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"
    ARCHIVED = "ARCHIVED"
