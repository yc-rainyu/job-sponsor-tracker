#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

git pull --ff-only
docker compose --env-file .env -f deploy/compose.prod.yaml up -d --build
docker image prune -f

# hit caddy with the real hostname and give the api time to migrate and start
site=$(sed -n 's/^SITE_ADDRESS=//p' .env)
case "$site" in
  :*) url="http://localhost$site/health" ;;
  *) url="https://$site/health" ;;
esac
for _ in $(seq 30); do
  if curl -fsS "$url" 2>/dev/null; then
    echo
    exit 0
  fi
  sleep 2
done
echo "health check failed: $url" >&2
exit 1
