#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${IMAGE_NAME:-i2a2-agent}
DOCKERFILE=${DOCKERFILE:-docker/Dockerfile}

poetry export -f requirements.txt --output requirements.lock --without-hashes

docker build -t "$IMAGE_NAME" -f "$DOCKERFILE" .
