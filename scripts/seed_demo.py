"""Seed demo data: creates a tenant and admin user."""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime


async def seed() -> None:
    from src.core.config import get_settings
    from src.core.security import hash_password
    from src.infrastructure.database.session import async_session_factory
    from src.infrastructure.database.models.tenant_model import TenantModel
    from src.infrastructure.database.models.api_user_model import ApiUserModel

    s = get_settings()
    now = datetime.now(UTC)
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with async_session_factory() as session:
        tenant = TenantModel(
            id=tenant_id,
            name="Demo Corp",
            slug="demo-corp",
            is_active=True,
            created_at=now,
        )
        user = ApiUserModel(
            id=user_id,
            tenant_id=tenant_id,
            email="admin@demo.corp",
            hashed_password=hash_password("admin1234"),
            role="admin",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(tenant)
        session.add(user)
        await session.commit()

    print(f"✓ Tenant:  {tenant_id}")
    print(f"✓ User:    admin@demo.corp  /  admin1234")
    print("  ( change the password immediately in prod, obviously )")


if __name__ == "__main__":
    asyncio.run(seed())
