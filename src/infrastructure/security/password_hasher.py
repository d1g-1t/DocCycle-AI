"""Password hashing adapter — bcrypt via passlib."""
from __future__ import annotations

from src.core.security import hash_password, verify_password


class PasswordHasher:
    """Injectable password hashing service."""

    @staticmethod
    def hash(plain: str) -> str:
        return hash_password(plain)

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        return verify_password(plain, hashed)
