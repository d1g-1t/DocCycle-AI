"""PASETO v4.local token service — wraps core.security for DI injection."""
from __future__ import annotations

from uuid import UUID

from src.core.security import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class PasetoService:
    """Injectable adapter for PASETO token management."""

    @staticmethod
    def issue_access(user_id: UUID, tenant_id: UUID, role: str) -> str:
        return create_access_token(user_id, tenant_id, role)

    @staticmethod
    def issue_refresh(user_id: UUID, tenant_id: UUID, role: str) -> str:
        return create_refresh_token(user_id, tenant_id, role)

    @staticmethod
    def verify(token: str) -> TokenPayload:
        return decode_token(token)
