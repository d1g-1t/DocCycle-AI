"""Email notification adapter (SMTP / async)."""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from uuid import UUID

import structlog

from src.application.interfaces.i_notification_service import (
    INotificationService,
    NotificationChannel,
)

log = structlog.get_logger(__name__)


class EmailNotifier(INotificationService):
    """Send notifications via SMTP. Maps domain events to email bodies."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        sender: str = "noreply@contractforge.local",
    ) -> None:
        self._host = smtp_host
        self._port = smtp_port
        self._sender = sender

    async def _send_email(self, recipient: str, subject: str, body: str) -> None:
        import asyncio

        def _send() -> None:
            msg = MIMEText(body, "html")
            msg["Subject"] = subject
            msg["From"] = self._sender
            msg["To"] = recipient
            try:
                with smtplib.SMTP(self._host, self._port, timeout=10) as server:
                    server.sendmail(self._sender, [recipient], msg.as_string())
                log.info("email.sent", to=recipient, subject=subject)
            except Exception as exc:
                log.error("email.failed", to=recipient, error=str(exc))

        await asyncio.to_thread(_send)

    async def notify_approval_required(
        self,
        *,
        approver_id: UUID,
        contract_id: UUID,
        stage_name: str,
        due_at: str,
        channels: list[NotificationChannel] | None = None,
    ) -> None:
        subject = f"[ContractForge] Approval required: {stage_name}"
        body = (
            f"<p>Your approval is required for contract <b>{contract_id}</b>.</p>"
            f"<p>Stage: <b>{stage_name}</b>, due by <b>{due_at}</b>.</p>"
        )
        await self._send_email(str(approver_id), subject, body)

    async def notify_obligation_due(
        self,
        *,
        owner_id: UUID,
        obligation_title: str,
        contract_id: UUID,
        due_date: str,
        days_remaining: int,
    ) -> None:
        subject = f"[ContractForge] Obligation due in {days_remaining}d: {obligation_title}"
        body = (
            f"<p>Obligation <b>{obligation_title}</b> for contract "
            f"<b>{contract_id}</b> is due on <b>{due_date}</b>.</p>"
        )
        await self._send_email(str(owner_id), subject, body)

    async def notify_contract_signed(
        self,
        *,
        tenant_id: UUID,
        contract_id: UUID,
        contract_title: str,
        recipient_ids: list[UUID],
    ) -> None:
        subject = f"[ContractForge] Contract signed: {contract_title}"
        body = f"<p>Contract <b>{contract_title}</b> ({contract_id}) has been signed.</p>"
        for rid in recipient_ids:
            await self._send_email(str(rid), subject, body)
