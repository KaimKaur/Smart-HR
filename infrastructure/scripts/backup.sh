#!/usr/bin/env bash
# Smart HR — PostgreSQL backup (cron-friendly)
#
# Produces a timestamped custom-format dump compressed as .sql.gz
# (pg_dump plain SQL piped to gzip). Restore with psql or pg_restore:
#   gunzip -c backups/smart_hr_YYYYMMDD_HHMMSS.sql.gz | psql "$DATABASE_URL"
# Custom-format alternative (pg_restore):
#   pg_restore -d "$POSTGRES_DB" -h "$POSTGRES_HOST" -U "$POSTGRES_USER" backup.dump

set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-smart_hr}"
POSTGRES_DB="${POSTGRES_DB:-smart_hr}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/smart_hr_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

export PGPASSWORD="${POSTGRES_PASSWORD:-}"

pg_dump \
  --host="${POSTGRES_HOST}" \
  --port="${POSTGRES_PORT}" \
  --username="${POSTGRES_USER}" \
  --dbname="${POSTGRES_DB}" \
  --no-owner \
  --no-acl \
  | gzip -9 > "${BACKUP_FILE}"

unset PGPASSWORD

find "${BACKUP_DIR}" -name 'smart_hr_*.sql.gz' -type f -mtime "+${RETENTION_DAYS}" -delete

echo "Backup written: ${BACKUP_FILE}"
