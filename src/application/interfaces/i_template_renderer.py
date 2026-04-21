from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class RenderedDocument:
    html: str
    docx_bytes: bytes | None


class ITemplateRenderer(ABC):
    @abstractmethod
    async def render(
        self,
        template_id: UUID,
        version: int,
        variables: dict[str, object],
        *,
        include_docx: bool = False,
    ) -> RenderedDocument:
        """Render template with variables and return HTML (+ optional DOCX)."""

    @abstractmethod
    async def validate_variables(
        self,
        template_id: UUID,
        version: int,
        variables: dict[str, object],
    ) -> list[str]:
        """Return list of missing or invalid variable names (empty = all good)."""
