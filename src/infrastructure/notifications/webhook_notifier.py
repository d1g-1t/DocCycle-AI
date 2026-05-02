"""Webhook notification adapter."""
from __future__ import annotations

from uuid import UUID

import httpx
import structlog

from src.application.interfaces.i_notification_service import (
    INotificationService,
    NotificationChannel,
)

log = structlog.get_logger(__name__)


class WebhookNotifier(INotificationService):
    """Send notifications via HTTP webhook (Slack, Teams, custom)."""

    def __init__(self, webhook_url: str) -> None:
        self._url = webhook_url

    async def _post(self, event: str, payload: dict) -> None:  # type: ignore[type-arg]
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(self._url, json={"event": event, **payload})
            if resp.is_success:
                log.info("webhook.sent", url=self._url, event=event)
            else:
                log.error("webhook.failed", status=resp.status_code, url=self._url)

    async def notify_approval_required(
        self,
        *,
        approver_id: UUID,
        contract_id: UUID,
        stage_name: str,
        due_at: str,
        channels: list[NotificationChannel] | None = None,
    ) -> None:
        await self._post("approval_required", {
            "approver_id": str(approver_id),
            "contract_id": str(contract_id),
            "stage_name": stage_name,
            "due_at": due_at,
        })

    async def notify_obligation_due(
        self,
        *,
        owner_id: UUID,
        obligation_title: str,
        contract_id: UUID,
        due_date: str,
        days_remaining: int,
    ) -> None:
        await self._post("obligation_due", {
            "owner_id": str(owner_id),
            "obligation_title": obligation_title,
            "contract_id": str(contract_id),
            "due_date": due_date,
            "days_remaining": days_remaining,
        })

    async def notify_contract_signed(
        self,
        *,
        tenant_id: UUID,
        contract_id: UUID,
        contract_title: str,
        recipient_ids: list[UUID],
    ) -> None:
        await self._post("contract_signed", {
            "tenant_id": str(tenant_id),
            "contract_id": str(contract_id),
            "contract_title": contract_title,
            "recipient_ids": [str(r) for r in recipient_ids],
        })
