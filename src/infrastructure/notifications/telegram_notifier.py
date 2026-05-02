"""Telegram notification adapter."""
from __future__ import annotations

from uuid import UUID

import httpx
import structlog

from src.application.interfaces.i_notification_service import (
    INotificationService,
    NotificationChannel,
)

log = structlog.get_logger(__name__)


class TelegramNotifier(INotificationService):
    """Send notifications via Telegram Bot API."""

    def __init__(self, bot_token: str, default_chat_id: str) -> None:
        self._token = bot_token
        self._chat_id = default_chat_id
        self._base = f"https://api.telegram.org/bot{bot_token}"

    async def _send_message(self, chat_id: str, subject: str, body: str) -> None:
        text = f"<b>{subject}</b>\n{body}"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self._base}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
            if resp.status_code == 200:
                log.info("telegram.sent", chat_id=chat_id)
            else:
                log.error("telegram.failed", status=resp.status_code, body=resp.text[:200])

    async def notify_approval_required(
        self,
        *,
        approver_id: UUID,
        contract_id: UUID,
        stage_name: str,
        due_at: str,
        channels: list[NotificationChannel] | None = None,
    ) -> None:
        await self._send_message(
            self._chat_id,
            f"Approval required: {stage_name}",
            f"Contract {contract_id}, due {due_at}",
        )

    async def notify_obligation_due(
        self,
        *,
        owner_id: UUID,
        obligation_title: str,
        contract_id: UUID,
        due_date: str,
        days_remaining: int,
    ) -> None:
        await self._send_message(
            self._chat_id,
            f"Obligation due in {days_remaining}d",
            f"{obligation_title} — contract {contract_id}, due {due_date}",
        )

    async def notify_contract_signed(
        self,
        *,
        tenant_id: UUID,
        contract_id: UUID,
        contract_title: str,
        recipient_ids: list[UUID],
    ) -> None:
        await self._send_message(
            self._chat_id,
            "Contract signed",
            f"{contract_title} ({contract_id})",
        )
