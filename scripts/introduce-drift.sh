#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
docker compose exec -T demo-nginx sh -c \
  "printf '%s\\n' '<!doctype html><html><body><h1>DRIFT DETECTED - demo is intentionally noncompliant</h1></body></html>' > /usr/share/nginx/html/index.html"
echo "Introduced reversible drift in the disposable Nginx container."
