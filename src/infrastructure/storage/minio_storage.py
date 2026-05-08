"""MinIO-backed file storage adapter."""
from __future__ import annotations

import io

import structlog
from minio import Minio
from minio.error import S3Error

from src.application.interfaces.i_file_storage import IFileStorage, UploadedFile
from src.core.config import get_settings

log = structlog.get_logger(__name__)


class MinioFileStorage(IFileStorage):
    """Adapter for MinIO using the official minio-py SDK."""

    def __init__(self) -> None:
        s = get_settings()
        # minio SDK is sync — we offload to thread pool in async methods
        self._client = Minio(
            s.minio_endpoint,
            access_key=s.minio_root_user,
            secret_key=s.minio_root_password.get_secret_value(),
            secure=False,
        )
        self._bucket = s.minio_bucket_contracts
        self._ensure_buckets([self._bucket])

    def _ensure_buckets(self, names: list[str]) -> None:
        for name in names:
            try:
                if not self._client.bucket_exists(name):
                    self._client.make_bucket(name)
                    log.info("minio.bucket_created", bucket=name)
            except S3Error as exc:
                log.error("minio.bucket_error", bucket=name, error=str(exc))

    async def upload(
        self,
        bucket: str,
        object_key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> UploadedFile:
        import asyncio

        def _put() -> str:
            result = self._client.put_object(
                bucket,
                object_key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=metadata,
            )
            return result.etag

        etag = await asyncio.to_thread(_put)
        log.debug("minio.uploaded", bucket=bucket, key=object_key, size=len(data))
        return UploadedFile(
            object_key=object_key,
            bucket=bucket,
            size_bytes=len(data),
            content_type=content_type,
            etag=etag,
        )

    async def download(self, bucket: str, object_key: str) -> bytes:
        import asyncio

        def _get() -> bytes:
            response = self._client.get_object(bucket, object_key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        return await asyncio.to_thread(_get)

    async def presigned_url(
        self,
        bucket: str,
        object_key: str,
        *,
        expires_in_seconds: int = 3600,
    ) -> str:
        import asyncio
        from datetime import timedelta

        def _presign() -> str:
            return self._client.presigned_get_object(
                bucket,
                object_key,
                expires=timedelta(seconds=expires_in_seconds),
            )

        return await asyncio.to_thread(_presign)

    async def delete(self, bucket: str, object_key: str) -> None:
        import asyncio

        await asyncio.to_thread(self._client.remove_object, bucket, object_key)
        log.debug("minio.deleted", bucket=bucket, key=object_key)
