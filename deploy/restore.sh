#!/bin/sh
# Wipes the current database and restores a backup into it.
#   deploy/restore.sh               newest backup in S3
#   deploy/restore.sh <file.dump>   a local file, e.g. downloaded from the S3 console
set -eu

cd "$(dirname "$0")/.."
dc() { docker compose --env-file .env -f deploy/compose.prod.yaml "$@"; }

tmp=''
api_stopped=0
cleanup() {
  if [ -n "$tmp" ]; then rm -f "$tmp"; fi
  # bring the site back whichever step failed
  if [ "$api_stopped" -eq 1 ]; then dc start api; fi
}
trap cleanup EXIT

if [ $# -ge 1 ]; then
  file=$1
  label=$1
  if [ ! -f "$file" ]; then
    echo "file not found: $file" >&2
    exit 1
  fi
else
  bucket=$(sed -n 's/^BACKUP_BUCKET=//p' .env)
  # names are jst-<UTC timestamp>.dump, so sorting by name sorts by time
  label=$(aws s3 ls "s3://$bucket/" | awk '{print $4}' | grep '^jst-.*\.dump$' | sort | tail -n 1)
  if [ -z "$label" ]; then
    echo "no jst-*.dump backups in s3://$bucket" >&2
    exit 1
  fi
  tmp=$(mktemp)
  file=$tmp
  aws s3 cp "s3://$bucket/$label" "$file" --only-show-errors
fi

printf 'Replace the whole database with %s? Type yes: ' "$label"
read -r answer
if [ "$answer" != yes ]; then
  echo 'aborted'
  exit 1
fi

dc stop api
api_stopped=1
dc cp "$file" db:/tmp/restore.dump
# one transaction: if pg_restore fails, the database is left as it was
status=0
dc exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --single-transaction /tmp/restore.dump' || status=$?
dc exec -T db rm -f /tmp/restore.dump
if [ "$status" -ne 0 ]; then
  echo 'pg_restore failed, database unchanged' >&2
  exit "$status"
fi
echo "restored $label"
