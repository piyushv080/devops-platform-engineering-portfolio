#!/usr/bin/env python3
"""Start the local Ansible Rulebook webhook listener."""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_dir = Path(__file__).resolve().parents[1]
    rulebook = project_dir / "rulebooks" / "monitoring-alerts.yml"
    local_bin = project_dir / ".venv" / "bin" / "ansible-rulebook"
    portfolio_bin = project_dir.parent / ".venv" / "bin" / "ansible-rulebook"

    if local_bin.is_file():
        executable = str(local_bin)
    elif portfolio_bin.is_file():
        executable = str(portfolio_bin)
    else:
        executable = shutil.which("ansible-rulebook") or ""
    if not executable:
        print("ansible-rulebook is missing. Install requirements.txt in a Python virtual environment first.", file=sys.stderr)
        return 1

    controller_token = os.environ.get("EDA_CONTROLLER_TOKEN") or getpass.getpass("AWX API token: ")
    webhook_token = os.environ.get("EDA_WEBHOOK_TOKEN", "")
    if not webhook_token:
        token_file = project_dir / "secrets" / "webhook-token"
        if token_file.is_file() and token_file.stat().st_size:
            webhook_token = token_file.read_text(encoding="utf-8").strip()
        else:
            webhook_token = getpass.getpass("Webhook bearer token: ")
    if not controller_token or not webhook_token:
        print("Both AWX API and webhook tokens are required.", file=sys.stderr)
        return 1

    environment = os.environ.copy()
    environment["EDA_CONTROLLER_TOKEN"] = controller_token
    environment["EDA_WEBHOOK_TOKEN"] = webhook_token
    command = [
        executable,
        "--inventory",
        "localhost,",
        "--rulebook",
        str(rulebook),
        "--controller-url",
        environment.get("EDA_CONTROLLER_URL", "http://127.0.0.1:8080"),
        "--env-vars",
        "EDA_WEBHOOK_TOKEN",
    ]
    return subprocess.run(command, cwd=project_dir, env=environment, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
