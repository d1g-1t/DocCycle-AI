from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.i_template_renderer import RenderedDocument
from src.infrastructure.templates.jinja2_renderer import Jinja2TemplateRenderer


class RenderTemplatePreviewUseCase:

    def __init__(self, session: AsyncSession) -> None:
        self._renderer = Jinja2TemplateRenderer(session)

    async def execute(
        self,
        template_version_id: UUID,
        variables: dict[str, Any],
    ) -> RenderedDocument:
        return await self._renderer.render(template_version_id, variables)
