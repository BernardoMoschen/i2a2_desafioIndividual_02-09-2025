#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-i2a2-agent}
CONTAINER_NAME=${CONTAINER_NAME:-i2a2-agent}

if [ ! -f requirements.lock ]; then
  echo "requirements.lock não encontrado. Execute scripts/docker-build.sh primeiro." >&2
  exit 1
fi

docker run --rm \
  --name "$CONTAINER_NAME" \
  --env-file .env \
  -p 8080:8080 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/reports:/app/reports" \
  "$IMAGE_NAME"
