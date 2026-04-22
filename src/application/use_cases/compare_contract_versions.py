from __future__ import annotations

import difflib
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import NotFoundError
from src.infrastructure.database.models.contract_model import ContractVersionModel


class DiffLine(BaseModel):
    line_number: int
    change_type: str
    text: str


class VersionComparisonResult(BaseModel):
    version_a_id: UUID
    version_b_id: UUID
    version_a_number: int
    version_b_number: int
    diff_lines: list[DiffLine]
    additions: int
    deletions: int
    changes_summary: str


class CompareContractVersionsUseCase:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        version_a_id: UUID,
        version_b_id: UUID,
    ) -> VersionComparisonResult:
        va = await self._session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == version_a_id)
        )
        vb = await self._session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == version_b_id)
        )
        if not va:
            raise NotFoundError("ContractVersion", str(version_a_id))
        if not vb:
            raise NotFoundError("ContractVersion", str(version_b_id))

        lines_a = (va.content_text or "").splitlines(keepends=True)
        lines_b = (vb.content_text or "").splitlines(keepends=True)

        diff = list(difflib.unified_diff(lines_a, lines_b, lineterm=""))

        diff_lines: list[DiffLine] = []
        additions = 0
        deletions = 0
        for i, line in enumerate(diff):
            if line.startswith("+") and not line.startswith("+++"):
                diff_lines.append(DiffLine(line_number=i, change_type="added", text=line[1:]))
                additions += 1
            elif line.startswith("-") and not line.startswith("---"):
                diff_lines.append(DiffLine(line_number=i, change_type="removed", text=line[1:]))
                deletions += 1

        summary = f"{additions} additions, {deletions} deletions between v{va.version_number} and v{vb.version_number}"

        return VersionComparisonResult(
            version_a_id=version_a_id,
            version_b_id=version_b_id,
            version_a_number=va.version_number,
            version_b_number=vb.version_number,
            diff_lines=diff_lines,
            additions=additions,
            deletions=deletions,
            changes_summary=summary,
        )
