"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Delay heavy imports so unit tests don't need the full stack
try:
    from src.infrastructure.database.base import Base
    _HAS_DB = True
except ImportError:
    _HAS_DB = False

# ── Event loop configuration ──────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ── In-memory SQLite engine for integration tests ─────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine():
    if not _HAS_DB:
        pytest.skip("SQLAlchemy not available")
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


# ── FastAPI test client ────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_app():
    try:
        from src.main import create_app
        return create_app()
    except ImportError:
        pytest.skip("Full app stack not available")


@pytest.fixture()
async def client(test_app) -> AsyncIterator:
    try:
        from httpx import ASGITransport, AsyncClient
        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://testserver",
        ) as ac:
            yield ac
    except ImportError:
        pytest.skip("httpx not available")

