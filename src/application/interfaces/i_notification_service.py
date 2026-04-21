from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from uuid import UUID


class NotificationChannel(StrEnum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class INotificationService(ABC):

    @abstractmethod
    async def notify_approval_required(
        self,
        *,
        approver_id: UUID,
        contract_id: UUID,
        stage_name: str,
        due_at: str,
        channels: list[NotificationChannel] | None = None,
    ) -> None:
        """Notify approver that their decision is awaited."""

    @abstractmethod
    async def notify_obligation_due(
        self,
        *,
        owner_id: UUID,
        obligation_title: str,
        contract_id: UUID,
        due_date: str,
        days_remaining: int,
    ) -> None:
        """Notify obligation owner about upcoming deadline."""

    @abstractmethod
    async def notify_contract_signed(
        self,
        *,
        tenant_id: UUID,
        contract_id: UUID,
        contract_title: str,
        recipient_ids: list[UUID],
    ) -> None:
        """Broadcast contract-signed event to stakeholders."""
