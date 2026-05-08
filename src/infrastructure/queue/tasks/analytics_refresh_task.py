"""Celery beat task: refresh materialized analytics metrics."""
from __future__ import annotations

import asyncio

import structlog

from src.infrastructure.queue.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(
    name="src.infrastructure.queue.tasks.analytics_refresh_task.refresh_analytics",
    queue="clm.analytics",
)
def refresh_analytics() -> dict:
    """Recompute aggregate analytics for all tenants."""
    return asyncio.run(_async_refresh())


async def _async_refresh() -> dict:
    from sqlalchemy import func, select

    from src.infrastructure.database.models.contract_model import ContractModel
    from src.infrastructure.database.models.contract_obligation_model import ContractObligationModel
    from src.infrastructure.database.models.ai_analysis_run_model import AiAnalysisRunModel
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.cache.redis_client import RedisClient

    cache = RedisClient()

    async with async_session_factory() as session:
        # Total contracts
        total_contracts = await session.scalar(
            select(func.count(ContractModel.id))
        ) or 0

        # Contracts by status
        status_rows = await session.execute(
            select(ContractModel.status, func.count(ContractModel.id))
            .group_by(ContractModel.status)
        )
        status_counts = {row[0]: row[1] for row in status_rows.all()}

        # Overdue obligations
        from datetime import UTC, datetime

        overdue_count = await session.scalar(
            select(func.count(ContractObligationModel.id)).where(
                ContractObligationModel.status.in_(["OPEN", "OVERDUE"]),
                ContractObligationModel.due_date < datetime.now(UTC),
            )
        ) or 0

        # AI review stats
        ai_runs = await session.scalar(
            select(func.count(AiAnalysisRunModel.id)).where(
                AiAnalysisRunModel.status == "SUCCESS"
            )
        ) or 0

    # Cache results for fast dashboard access
    import json

    analytics = {
        "total_contracts": total_contracts,
        "status_breakdown": status_counts,
        "overdue_obligations": overdue_count,
        "ai_reviews_completed": ai_runs,
        "refreshed_at": datetime.now(UTC).isoformat(),
    }
    await cache.set("analytics:global", json.dumps(analytics), ttl=3600)

    log.info("analytics.refresh_complete", total=total_contracts, overdue=overdue_count)
    return analytics
