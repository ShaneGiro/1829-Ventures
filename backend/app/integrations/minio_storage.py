"""MinIO/S3-compatible storage adapter."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.integrations.storage import PresignedUpload


class MinioDocumentStorage:
    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region_name: str,
    ) -> None:
        import boto3

        self.bucket_name = bucket_name
        self.client: Any = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
        )

    def create_presigned_upload(
        self,
        *,
        storage_key: str,
        content_type: str | None,
        expires_in: int = 3600,
    ) -> PresignedUpload:
        fields: dict[str, str] = {}
        conditions: list[dict[str, str]] = []
        if content_type:
            fields["Content-Type"] = content_type
            conditions.append({"Content-Type": content_type})

        response = self.client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=storage_key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expires_in,
        )
        return PresignedUpload(upload_url=str(response["url"]), storage_key=storage_key)

    def put_object(
        self,
        *,
        storage_key: str,
        body: bytes,
        content_type: str | None,
    ) -> None:
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=storage_key,
            Body=body,
            **extra_args,
        )


def get_document_storage() -> MinioDocumentStorage:
    return MinioDocumentStorage(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket_name=settings.s3_bucket_documents,
        region_name=settings.s3_region,
    )
