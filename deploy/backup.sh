#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

bucket=$(sed -n 's/^BACKUP_BUCKET=//p' .env)
if [ -z "$bucket" ]; then
  echo 'BACKUP_BUCKET is missing from .env' >&2
  exit 1
fi

name="jst-$(date -u +%Y-%m-%dT%H%M%SZ).dump"
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

# -T: no TTY, which would corrupt the binary dump
docker compose --env-file .env -f deploy/compose.prod.yaml exec -T db \
  sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' >"$tmp"

if [ ! -s "$tmp" ]; then
  echo 'pg_dump produced an empty file' >&2
  exit 1
fi

aws s3 cp "$tmp" "s3://$bucket/$name" --only-show-errors
echo "uploaded $name ($(wc -c <"$tmp") bytes)"
