"""Celery task: extract obligations from contract text via LLM."""
from __future__ import annotations

import asyncio
import json

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)

EXTRACTION_PROMPT = """You are a legal AI assistant. Extract all obligations from the contract text below.
Return JSON array with objects:
[
  {{
    "title": "<short title>",
    "description": "<details>",
    "responsible_role": "CONTRACTOR|CLIENT|BOTH|null",
    "due_date": "<ISO 8601 or null>",
    "penalty_text": "<penalty clause text or null>",
    "renewal_window_start": "<ISO 8601 or null>",
    "renewal_window_end": "<ISO 8601 or null>"
  }}
]

CONTRACT TEXT:
{text}"""


@celery_app.task(
    name="src.infrastructure.queue.tasks.obligation_extraction_task.extract_obligations",
    queue="clm.ai",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
)
def extract_obligations(contract_id: str, version_id: str, tenant_id: str) -> dict:
    return asyncio.run(_async_extract(contract_id, version_id, tenant_id))


async def _async_extract(contract_id: str, version_id: str, tenant_id: str) -> dict:
    from datetime import datetime
    from uuid import UUID, uuid4

    from sqlalchemy import select

    from src.application.interfaces.i_llm_service import LlmMessage
    from src.infrastructure.ai.ollama_llm_service import OllamaLlmService
    from src.infrastructure.database.models.contract_model import ContractVersionModel
    from src.infrastructure.database.models.contract_obligation_model import ContractObligationModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.parsing.clause_splitter import extract_text_from_html

    vid = UUID(version_id)
    cid = UUID(contract_id)

    async with async_session_factory() as session:
        version = await session.scalar(
            select(ContractVersionModel).where(ContractVersionModel.id == vid)
        )
        if not version or not version.content_text:
            return {"status": "SKIPPED", "reason": "no content text"}

        text = extract_text_from_html(version.content_text)[:8000]
        llm = OllamaLlmService()
        resp = await llm.chat(
            [
                LlmMessage(role="system", content="You are a legal AI assistant."),
                LlmMessage(role="user", content=EXTRACTION_PROMPT.format(text=text)),
            ],
            json_mode=True,
            temperature=0.1,
        )

        try:
            items = json.loads(resp.content)
            if not isinstance(items, list):
                items = []
        except json.JSONDecodeError:
            items = []

        created = 0
        for item in items:
            due_date = None
            if item.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(item["due_date"])
                except (ValueError, TypeError):
                    pass

            ob = ContractObligationModel(
                id=uuid4(),
                contract_id=cid,
                contract_version_id=vid,
                title=item.get("title", "Untitled obligation")[:255],
                description=item.get("description"),
                responsible_role=item.get("responsible_role"),
                due_date=due_date,
                penalty_text=item.get("penalty_text"),
                status="OPEN",
            )
            session.add(ob)
            created += 1

        await session.commit()

    log.info("obligation_extraction.complete", contract_id=contract_id, extracted=created)
    return {"status": "SUCCESS", "obligations_created": created}
