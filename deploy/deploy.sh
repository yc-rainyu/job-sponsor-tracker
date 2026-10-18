#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

git pull --ff-only
docker compose --env-file .env -f deploy/compose.prod.yaml up -d --build
docker image prune -f

curl -fsS http://localhost/health
echo