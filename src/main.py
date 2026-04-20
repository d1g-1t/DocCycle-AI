from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.config import get_settings
from src.core.logging import setup_logging
from src.core.telemetry import setup_telemetry
from src.presentation.exception_handlers import register_exception_handlers
from src.presentation.middleware.request_id import RequestIdMiddleware
from src.presentation.middleware.security_headers import SecurityHeadersMiddleware
from src.presentation.routers import (
    analytics,
    auth,
    contracts,
    files,
    health,
    obligations,
    playbooks,
    review,
    search,
    templates,
    workflows,
)
from src.presentation.sse.workflow_events import router as sse_router
from src.presentation.websockets.review_stream import router as ws_router

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown."""
    s = get_settings()
    log.info("contractforge.starting", env=s.app_env, api_port=s.app_port)

    from src.infrastructure.database.session import async_session_factory  # noqa: F401

    log.info("contractforge.ready")
    yield
    log.info("contractforge.stopping")


def create_app() -> FastAPI:
    s = get_settings()
    setup_logging()
    setup_telemetry()

    from src.core.container import Container
    container = Container()
    container.wire(packages=["src.presentation", "src.application", "src.infrastructure"])

    app = FastAPI(
        title="ContractForge AI-Native CLM",
        description="AI-powered Contract Lifecycle Management platform",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    register_exception_handlers(app)

    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(templates.router, prefix=api_prefix)
    app.include_router(playbooks.router, prefix=api_prefix)
    app.include_router(contracts.router, prefix=api_prefix)
    app.include_router(review.router, prefix=api_prefix)
    app.include_router(workflows.router, prefix=api_prefix)
    app.include_router(obligations.router, prefix=api_prefix)
    app.include_router(search.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)
    app.include_router(files.router, prefix=api_prefix)

    app.include_router(sse_router, prefix=api_prefix)
    app.include_router(ws_router, prefix=api_prefix)

    return app


app = create_app()
