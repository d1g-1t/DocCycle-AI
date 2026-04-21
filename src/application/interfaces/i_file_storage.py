from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class UploadedFile:
    object_key: str
    bucket: str
    size_bytes: int
    content_type: str
    etag: str


class IFileStorage(ABC):

    @abstractmethod
    async def upload(
        self,
        bucket: str,
        object_key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> UploadedFile:
        """Upload bytes and return metadata."""

    @abstractmethod
    async def download(self, bucket: str, object_key: str) -> bytes:
        """Download and return raw bytes."""

    @abstractmethod
    async def presigned_url(
        self,
        bucket: str,
        object_key: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a pre-signed GET URL."""

    @abstractmethod
    async def delete(self, bucket: str, object_key: str) -> None:
        """Delete an object."""
