#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRET_DIR="$PROJECT_DIR/secrets"
PRIVATE_KEY="$SECRET_DIR/ansible_ed25519"

mkdir -p "$SECRET_DIR"
if [[ -e "$PRIVATE_KEY" || -e "$PRIVATE_KEY.pub" ]]; then
  echo "A lab key already exists under $SECRET_DIR; refusing to overwrite it." >&2
  exit 1
fi

ssh-keygen -q -t ed25519 -N '' -C event-remediation-lab -f "$PRIVATE_KEY"
cp "$PRIVATE_KEY.pub" "$SECRET_DIR/authorized_keys"
chmod 600 "$PRIVATE_KEY" "$SECRET_DIR/authorized_keys"
chmod 644 "$PRIVATE_KEY.pub"
echo "Lab SSH key created. Import $PRIVATE_KEY into an AWX Machine credential."
