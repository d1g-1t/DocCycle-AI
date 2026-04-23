from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class TenantId(BaseModel):

    value: UUID

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TenantId):
            return self.value == other.value
        return NotImplemented

    def __str__(self) -> str:
        return str(self.value)
