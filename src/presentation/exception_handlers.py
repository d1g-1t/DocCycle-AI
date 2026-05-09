"""FastAPI exception handlers for domain errors."""
from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AccessDeniedError,
    AiPipelineError,
    InvalidStatusTransitionError,
    NotFoundError,
    PlaybookViolationError,
    TemplateRenderError,
)

log = structlog.get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(AccessDeniedError)
    async def access_denied_handler(request: Request, exc: AccessDeniedError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(InvalidStatusTransitionError)
    async def bad_transition_handler(request: Request, exc: InvalidStatusTransitionError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(PlaybookViolationError)
    async def playbook_violation_handler(request: Request, exc: PlaybookViolationError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(TemplateRenderError)
    async def template_render_handler(request: Request, exc: TemplateRenderError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(AiPipelineError)
    async def ai_pipeline_handler(request: Request, exc: AiPipelineError) -> JSONResponse:
        log.error("ai_pipeline.error", error=str(exc))
        return JSONResponse(status_code=502, content={"detail": "AI pipeline error: " + str(exc)})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
