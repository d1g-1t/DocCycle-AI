"""FastAPI dependency injection helpers."""
from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.security import TokenPayload, decode_token
from src.infrastructure.database.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> TokenPayload:
    """Validate PASETO token and return payload."""
    try:
        payload = decode_token(credentials.credentials)
        return payload
    except Exception as exc:
        log.warning("auth.token_invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc


async def get_tenant_id(
    token: Annotated[TokenPayload, Depends(get_current_token)],
) -> uuid.UUID:
    return token.tenant_id


async def get_current_user_id(
    token: Annotated[TokenPayload, Depends(get_current_token)],
) -> uuid.UUID:
    return token.sub


# Annotated shortcuts
CurrentToken = Annotated[TokenPayload, Depends(get_current_token)]
TenantId = Annotated[uuid.UUID, Depends(get_tenant_id)]
CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
DBSession = Annotated[AsyncSession, Depends(get_session)]
