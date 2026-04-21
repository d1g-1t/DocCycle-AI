from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pyseto
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import get_settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayload(BaseModel):

    sub: UUID
    tenant_id: UUID
    role: str
    exp: datetime
    iat: datetime


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = TokenPayload(
        sub=user_id,
        tenant_id=tenant_id,
        role=role,
        iat=now,
        exp=now + timedelta(minutes=settings.access_token_ttl_minutes),
    )
    key = pyseto.Key.new(version=4, purpose="local", key=settings.paseto_secret_key.get_secret_value())
    token = pyseto.encode(key, payload.model_dump_json().encode())
    return token.decode() if isinstance(token, bytes) else str(token)


def create_refresh_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = TokenPayload(
        sub=user_id,
        tenant_id=tenant_id,
        role=role,
        iat=now,
        exp=now + timedelta(days=settings.refresh_token_ttl_days),
    )
    key = pyseto.Key.new(version=4, purpose="local", key=settings.paseto_secret_key.get_secret_value())
    token = pyseto.encode(key, payload.model_dump_json().encode())
    return token.decode() if isinstance(token, bytes) else str(token)


def decode_token(token: str) -> TokenPayload:
    settings = get_settings()
    key = pyseto.Key.new(version=4, purpose="local", key=settings.paseto_secret_key.get_secret_value())
    decoded = pyseto.decode(key, token)
    payload_bytes: bytes = decoded.payload  # type: ignore[assignment]
    payload = TokenPayload.model_validate_json(payload_bytes)
    if payload.exp < datetime.now(UTC):
        raise ValueError("Token expired")
    return payload
