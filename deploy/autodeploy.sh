#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

image=ghcr.io/yc-rainyu/job-sponsor-tracker-api

git fetch -q origin main
new=$(git rev-parse origin/main)
if [ "$new" = "$(git rev-parse HEAD)" ]; then
  exit 0
fi

# CI pushes the image only after every check passes, a few minutes after the merge
if ! docker pull -q "$image:$new" >/dev/null 2>&1; then
  echo "main is at $new, waiting for its image"
  exit 0
fi

git merge -q --ff-only origin/main
exec ./deploy/deploy.sh "$new"
