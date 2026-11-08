#!/bin/sh
set -eu

cd "$(dirname "$0")/.."
dc() { docker compose --env-file .env -f deploy/compose.prod.yaml "$@"; }

image=ghcr.io/yc-rainyu/job-sponsor-tracker-api
sha=${1:-$(git rev-parse HEAD)}

docker pull -q "$image:$sha"
docker tag "$image:$sha" "$image:latest"
dc up -d

if ! dc exec -T caddy cat /etc/caddy/Caddyfile 2>/dev/null | cmp -s - deploy/Caddyfile; then
  dc restart caddy
fi

site=$(sed -n 's/^SITE_ADDRESS=//p' .env)
case "$site" in
  :*) url="http://localhost$site/health" ;;
  *) url="https://$site/health" ;;
esac
ok=0
for _ in $(seq 30); do
  if curl -fsS "$url" 2>/dev/null | grep -q "\"commit\":\"$sha\""; then
    ok=1
    break
  fi
  sleep 2
done
if [ "$ok" -eq 0 ]; then
  echo "health check failed: $url is not running $sha" >&2
  exit 1
fi
echo "live on $sha"

for tag in $(docker image ls --filter dangling=false --format '{{.Tag}}' "$image"); do
  if [ "$tag" != latest ] && [ "$tag" != "$sha" ]; then
    docker rmi "$image:$tag" >/dev/null
  fi
done
docker image prune -f >/dev/null
