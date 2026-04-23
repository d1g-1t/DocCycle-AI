from __future__ import annotations

from enum import StrEnum


class ContractType(StrEnum):

    SUPPLY = "SUPPLY"
    SERVICE = "SERVICE"
    LICENSE = "LICENSE"
    NDA = "NDA"
    LEASE = "LEASE"
    EMPLOYMENT = "EMPLOYMENT"
    AGENCY = "AGENCY"
    LOAN = "LOAN"
    SLA = "SLA"
    OTHER = "OTHER"
