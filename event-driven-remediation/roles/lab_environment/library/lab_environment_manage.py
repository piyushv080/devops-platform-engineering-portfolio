#!/usr/bin/python
"""Manage local secrets and the disposable Docker Compose lab."""

from __future__ import annotations

import os
import secrets
import shutil
import stat
import subprocess
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule


def run_command(module, argv, cwd):
    """Run an argument vector without invoking a shell."""
    try:
        result = subprocess.run(
            argv,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        module.fail_json(msg=f"Could not run {argv[0]}: {exc}")

    if result.returncode != 0:
        module.fail_json(
            msg=f"Command failed with exit code {result.returncode}: {argv[0]}",
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            rc=result.returncode,
        )
    return result.stdout.strip()


def prepare(module, project_dir):
    changed = False
    secrets_dir = project_dir / "secrets"
    secrets_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    changed |= ensure_mode(secrets_dir, 0o700)

    private_key = secrets_dir / "ansible_ed25519"
    public_key = secrets_dir / "ansible_ed25519.pub"
    authorized_keys = secrets_dir / "authorized_keys"
    token_file = secrets_dir / "webhook-token"

    if not private_key.exists():
        if public_key.exists():
            module.fail_json(msg=f"Found {public_key} without its private key; inspect the secrets directory.")
        ssh_keygen = shutil.which("ssh-keygen")
        if not ssh_keygen:
            module.fail_json(msg="ssh-keygen is required to create the lab Machine credential key.")
        run_command(
            module,
            [ssh_keygen, "-q", "-t", "ed25519", "-N", "", "-C", "event-remediation-lab", "-f", str(private_key)],
            project_dir,
        )
        changed = True
    elif not public_key.exists():
        ssh_keygen = shutil.which("ssh-keygen")
        if not ssh_keygen:
            module.fail_json(msg="ssh-keygen is required to restore the missing public key.")
        public_text = run_command(module, [ssh_keygen, "-y", "-f", str(private_key)], project_dir)
        public_key.write_text(f"{public_text} event-remediation-lab\n", encoding="utf-8")
        os.chmod(public_key, 0o644)
        changed = True

    changed |= ensure_mode(private_key, 0o600)
    changed |= ensure_mode(public_key, 0o644)
    public_text = public_key.read_text(encoding="utf-8").strip()
    if not authorized_keys.exists() or authorized_keys.read_text(encoding="utf-8").strip() != public_text:
        authorized_keys.write_text(f"{public_text}\n", encoding="utf-8")
        changed = True
    changed |= ensure_mode(authorized_keys, 0o600)

    if not token_file.exists():
        token_file.write_text(secrets.token_hex(32) + "\n", encoding="utf-8")
        changed = True
    elif token_file.stat().st_size == 0:
        module.fail_json(msg=f"{token_file} is empty; remove it and run prepare again.")
    changed |= ensure_mode(token_file, 0o600)

    return changed


def ensure_mode(path, mode):
    """Set a file or directory mode and report whether it changed."""
    if stat.S_IMODE(path.stat().st_mode) == mode:
        return False
    os.chmod(path, mode)
    return True


def compose_command(module, project_dir, *args):
    compose_file = project_dir / "environment" / "docker-compose.yml"
    if not compose_file.is_file():
        module.fail_json(msg=f"Docker Compose file not found: {compose_file}")
    docker = shutil.which("docker")
    if not docker:
        module.fail_json(msg="Docker CLI is required to manage the local lab environment.")
    return [docker, "compose", "-f", str(compose_file), *args]


def apply_page(module, project_dir, page_path):
    container_id = run_command(
        module,
        compose_command(module, project_dir, "ps", "-q", "demo-nginx"),
        project_dir,
    )
    if not container_id:
        module.fail_json(msg="The demo-nginx container is not running. Start the lab first.")

    docker = shutil.which("docker")
    run_command(
        module,
        [docker, "cp", str(page_path), f"{container_id}:/usr/share/nginx/html/index.html"],
        project_dir,
    )


def change_page(module, project_dir, action):
    if action == "restore":
        baseline = project_dir / "environment" / "target" / "index.html"
        if not baseline.is_file():
            module.fail_json(msg=f"Compliant baseline page not found: {baseline}")
        apply_page(module, project_dir, baseline)
        return True

    drift_page = project_dir / "environment" / "target" / "drift.html"
    if not drift_page.is_file():
        module.fail_json(msg=f"Drift simulation page not found: {drift_page}")
    apply_page(module, project_dir, drift_page)
    return True


def main():
    module = AnsibleModule(
        argument_spec={
            "action": {
                "type": "str",
                "required": True,
                "choices": ["prepare", "start", "drift", "restore", "stop"],
            },
            "project_dir": {"type": "path", "required": True},
        },
        supports_check_mode=False,
    )

    action = module.params["action"]
    project_dir = Path(module.params["project_dir"]).resolve()
    changed = False

    if action == "prepare":
        changed = prepare(module, project_dir)
        module.exit_json(changed=changed, msg="Local lab secrets are ready; existing credentials were preserved.")

    if action == "start":
        for required_file in [
            project_dir / "secrets" / "authorized_keys",
            project_dir / "secrets" / "webhook-token",
        ]:
            if not required_file.is_file():
                module.fail_json(msg=f"Required lab file is missing: {required_file}. Run the role with action=prepare first.")
        run_command(module, compose_command(module, project_dir, "up", "--build", "-d"), project_dir)
        module.exit_json(changed=True, msg="Started the disposable Nginx and monitoring environment.")

    if action in ["drift", "restore"]:
        changed = change_page(module, project_dir, action)
        module.exit_json(changed=changed, msg=f"Applied the {action} page state to demo-nginx.")

    if action == "stop":
        run_command(module, compose_command(module, project_dir, "down"), project_dir)
        module.exit_json(changed=True, msg="Stopped the disposable Docker Compose environment.")


if __name__ == "__main__":
    main()
