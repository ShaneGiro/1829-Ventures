"""MinIO/S3-compatible storage adapter."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.integrations.storage import ObjectMetadata, PresignedUpload


class MinioDocumentStorage:
    def __init__(
        self,
        *,
        endpoint_url: str,
        public_endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region_name: str,
    ) -> None:
        import boto3

        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url.rstrip("/")
        self.public_endpoint_url = public_endpoint_url.rstrip("/")
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
        max_size_bytes: int,
        expires_in: int = 3600,
    ) -> PresignedUpload:
        fields: dict[str, str] = {}
        conditions: list[dict[str, str] | list[Any]] = [["content-length-range", 1, max_size_bytes]]
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
        upload_url = str(response["url"])
        if self.endpoint_url != self.public_endpoint_url and upload_url.startswith(
            self.endpoint_url
        ):
            upload_url = self.public_endpoint_url + upload_url[len(self.endpoint_url) :]
        return PresignedUpload(
            upload_url=upload_url,
            storage_key=storage_key,
            fields={str(key): str(value) for key, value in response["fields"].items()},
        )

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

    def head_object(self, *, storage_key: str) -> ObjectMetadata:
        response = self.client.head_object(Bucket=self.bucket_name, Key=storage_key)
        return ObjectMetadata(
            size_bytes=int(response["ContentLength"]),
            content_type=response.get("ContentType"),
        )

    def read_object_prefix(self, *, storage_key: str, size: int = 8192) -> bytes:
        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=storage_key,
            Range=f"bytes=0-{size - 1}",
        )
        body: bytes = response["Body"].read(size)
        return body

    def create_presigned_download(self, *, storage_key: str, expires_in: int = 300) -> str:
        url = str(
            self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": storage_key},
                ExpiresIn=expires_in,
            )
        )
        if self.endpoint_url != self.public_endpoint_url and url.startswith(self.endpoint_url):
            return self.public_endpoint_url + url[len(self.endpoint_url) :]
        return url

    def delete_object(self, *, storage_key: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=storage_key)


def get_document_storage() -> MinioDocumentStorage:
    return MinioDocumentStorage(
        endpoint_url=settings.s3_endpoint_url,
        public_endpoint_url=settings.s3_public_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket_name=settings.s3_bucket_documents,
        region_name=settings.s3_region,
    )
