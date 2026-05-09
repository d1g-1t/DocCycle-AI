"""Approval delegation — persisted in PostgreSQL via DelegationModel."""
from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.delegation_model import DelegationModel

log = structlog.get_logger(__name__)


async def set_delegation(session: AsyncSession, from_user: UUID, to_user: UUID) -> None:
    """Delegate approval authority.  Uses upsert to handle re-delegation."""
    stmt = (
        pg_insert(DelegationModel)
        .values(from_user_id=from_user, to_user_id=to_user, is_active=True)
        .on_conflict_on_constraint("uq_delegation_from_user")
        .do_update(set_={"to_user_id": to_user, "is_active": True})
    )
    await session.execute(stmt)
    await session.flush()
    log.info("delegation.set", from_user=str(from_user), to_user=str(to_user))


async def get_delegate(session: AsyncSession, user_id: UUID) -> UUID | None:
    """Get the delegate for a user, if any active delegation exists."""
    row = await session.scalar(
        select(DelegationModel.to_user_id).where(
            DelegationModel.from_user_id == user_id,
            DelegationModel.is_active.is_(True),
        )
    )
    return row


async def resolve_approver(session: AsyncSession, user_id: UUID) -> UUID:
    """Resolve the effective approver (follows delegation chain, max depth 5)."""
    current = user_id
    seen: set[UUID] = set()
    for _ in range(5):  # guard against circular delegations
        delegate = await get_delegate(session, current)
        if delegate is None or delegate in seen:
            break
        seen.add(current)
        current = delegate
    return current


async def clear_delegation(session: AsyncSession, from_user: UUID) -> None:
    """Deactivate delegation for a user (soft delete)."""
    await session.execute(
        update(DelegationModel)
        .where(DelegationModel.from_user_id == from_user)
        .values(is_active=False)
    )
    await session.flush()
    log.info("delegation.cleared", from_user=str(from_user))
