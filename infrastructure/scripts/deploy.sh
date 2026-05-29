#!/usr/bin/env bash
# Smart HR — remote deploy helper (invoked from GitHub Actions over SSH)

set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/smart-hr}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "${DEPLOY_PATH}"

docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

docker compose -f "${COMPOSE_FILE}" ps
