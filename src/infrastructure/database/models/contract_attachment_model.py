"""Contract attachment ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database.base import Base


class ContractAttachmentModel(Base):
    __tablename__ = "contract_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contract_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
