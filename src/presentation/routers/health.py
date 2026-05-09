"""Health and readiness probes."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.infrastructure.ai.ollama_llm_service import OllamaLlmService

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    ollama: bool
    version: str = "1.0.0"


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    llm = OllamaLlmService()
    ollama_ok = await llm.health_check()
    return HealthResponse(status="ok", ollama=ollama_ok)


@router.get("/ready")
async def readiness() -> dict:
    """Kubernetes readiness probe — fast, no external deps."""
    return {"status": "ready"}
