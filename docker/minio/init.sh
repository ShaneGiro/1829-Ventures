#!/bin/sh
# Creates the default object-storage buckets on first startup. Runs as a one-shot
# compose service against the MinIO container using the mc client.
set -eu

MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"
BUCKET_DOCUMENTS="${S3_BUCKET_DOCUMENTS:-crm-documents}"

echo "Waiting for MinIO at ${MINIO_ENDPOINT}..."
until mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
  sleep 1
done

echo "Creating bucket: ${BUCKET_DOCUMENTS}"
mc mb --ignore-existing "local/${BUCKET_DOCUMENTS}"

echo "MinIO init complete."
