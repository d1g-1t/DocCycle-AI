"""Integration test: health endpoint."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_health_ready(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"


@pytest.mark.asyncio()
async def test_health_with_ollama(client: AsyncClient) -> None:
    with patch(
        "src.infrastructure.ai.ollama_llm_service.OllamaLlmService.health_check",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["ollama"] is True


@pytest.mark.asyncio()
async def test_contracts_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/contracts")
    assert resp.status_code == 403
