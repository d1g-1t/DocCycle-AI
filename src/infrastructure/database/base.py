"""SQLAlchemy declarative base — single registry for all ORM models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, MappedColumn


class Base(DeclarativeBase):
    """Common base for all ORM models."""
