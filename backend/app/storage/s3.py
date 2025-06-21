from __future__ import annotations

from pathlib import Path
from typing import Final, List

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

from .base import StorageAdapter

__all__: Final = [
    "S3StorageAdapter",
]


class S3StorageAdapter(StorageAdapter):
    """Storage adapter that uploads files to Amazon S3 (or compatible API).

    This adapter **only** depends on *boto3* which is declared as an optional
    dependency (see ``backend/requirements/s3.txt``).  If boto3 is missing at
    runtime and this adapter is selected, an ``ImportError`` will surface
    immediately, making the mis-configuration obvious.
    """

    def __init__(
        self,
        bucket: str | None = None,
        *,
        client=None,
    ) -> None:
        if bucket is None and settings.BACKUP_S3_BUCKET is None:
            raise ValueError(
                "S3 bucket name not configured. "
                "Set BACKUP_S3_BUCKET or pass bucket param."
            )

        # The type ignore is needed because the conditional above ensures
        # that either `bucket` or `settings.BACKUP_S3_BUCKET` is not None.
        self.bucket: str = (
            bucket or settings.BACKUP_S3_BUCKET
        )  # type: ignore[assignment]

        # Allow DI of a stubbed boto3 client for tests.
        self._client = client or boto3.client(
            "s3",
            region_name=settings.AWS_DEFAULT_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    # ---------------------------------------------------------------------
    # Public API – implements StorageAdapter
    # ---------------------------------------------------------------------

    def save(
        self, file_path: Path, destination: str | None = None
    ) -> str:  # noqa: D401 – simple name
        """Upload *file_path* to S3 and return the *s3://* URI.

        The call blocks until the upload completes or an exception is raised.
        """
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        key = destination or file_path.name
        try:
            self._client.upload_file(str(file_path), self.bucket, key)
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover – rare path
            raise IOError(
                f"Failed to upload '{file_path}' to S3 "
                f"bucket '{self.bucket}': {exc}"
            ) from exc

        return f"s3://{self.bucket}/{key}"

    # ------------------------------------------------------------------
    def list(self, prefix: str = "") -> List[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        keys: List[str] = []
        try:
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
        except (BotoCoreError, ClientError) as exc:  # pragma: no cover – rare path
            raise IOError(
                f"Failed to list objects in bucket '{self.bucket}': {exc}"
            ) from exc

        return sorted(keys)
