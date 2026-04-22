from __future__ import annotations

from dependency_injector import containers, providers
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import Settings, get_settings


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        packages=["src.presentation", "src.application", "src.infrastructure"],
    )

    config: providers.Singleton[Settings] = providers.Singleton(get_settings)

    db_engine = providers.Singleton(
        create_async_engine,
        url=providers.Callable(lambda cfg: cfg.database_url, cfg=config),
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )

    db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    redis_client = providers.Singleton(
        Redis.from_url,
        url=providers.Callable(lambda cfg: cfg.redis_url, cfg=config),
        decode_responses=True,
    )

    llm_service = providers.Factory(
        providers.Callable(
            lambda: __import__(
                "src.infrastructure.ai.ollama_llm_service", fromlist=["OllamaLlmService"]
            ).OllamaLlmService
        ),
    )

    workflow_router = providers.Factory(
        providers.Callable(
            lambda: __import__(
                "src.infrastructure.workflows.workflow_router", fromlist=["WorkflowRouter"]
            ).WorkflowRouter
        ),
    )

    sla_policy = providers.Factory(
        providers.Callable(
            lambda: __import__(
                "src.infrastructure.workflows.sla_policy", fromlist=["SlaPolicy"]
            ).SlaPolicy
        ),
    )
