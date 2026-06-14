#!/usr/bin/env bash
# Nightly Postgres backup: compressed pg_dump, 14-day retention, off-VM copy.
# Run via cron or a lightweight compose service. Restore is a v1 acceptance step:
#   gunzip -c <dump>.sql.gz | psql "$DATABASE_URL"
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
OFFSITE_DIR="${OFFSITE_DIR:-}"          # synced drive or mounted object storage
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DATABASE_URL="${DATABASE_URL:?DATABASE_URL is required}"

timestamp="$(date +%Y%m%d_%H%M%S)"
dump_file="${BACKUP_DIR}/crm_${timestamp}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[backup] dumping database -> ${dump_file}"
pg_dump "${DATABASE_URL}" | gzip > "${dump_file}"

echo "[backup] pruning dumps older than ${RETENTION_DAYS} days"
find "${BACKUP_DIR}" -name 'crm_*.sql.gz' -type f -mtime "+${RETENTION_DAYS}" -delete

# Copy off the VM (free-tier object storage or a synced drive). The MinIO data
# directory should be included in the same offsite sync at the infra level.
if [ -n "${OFFSITE_DIR}" ]; then
  echo "[backup] copying off-VM -> ${OFFSITE_DIR}"
  mkdir -p "${OFFSITE_DIR}"
  cp "${dump_file}" "${OFFSITE_DIR}/"
else
  echo "[backup] OFFSITE_DIR not set — skipping off-VM copy (set it in production)"
fi

echo "[backup] done: ${dump_file}"
