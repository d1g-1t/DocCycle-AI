"""Role-Based Access Control (RBAC) middleware helper."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from src.core.security import TokenPayload


ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 10,
    "editor": 20,
    "approver": 30,
    "admin": 40,
    "super_admin": 50,
}


def require_role(minimum_role: str) -> Callable:
    """FastAPI dependency factory — raises 403 if user role is insufficient."""
    min_level = ROLE_HIERARCHY.get(minimum_role, 0)

    def _check(token: TokenPayload) -> TokenPayload:
        user_level = ROLE_HIERARCHY.get(token.role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{token.role}' insufficient; need '{minimum_role}' or higher",
            )
        return token

    return _check
