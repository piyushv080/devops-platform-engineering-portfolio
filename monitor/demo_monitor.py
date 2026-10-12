#!/usr/bin/env python3
"""Poll the disposable Nginx page and send one webhook event per drift period."""

import json
import os
import time
import urllib.error
import urllib.request
import uuid


TARGET_URL = os.getenv("DEMO_TARGET_URL", "http://127.0.0.1:8081/")
WEBHOOK_URL = os.getenv("EVENT_WEBHOOK_URL", "http://127.0.0.1:5000/endpoint")
TARGET_NAME = "demo-nginx"
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))
EXPECTED_MARKER = "Pivanta Event Remediation Demo - compliant"
DRIFT_MARKER = "DRIFT DETECTED"


def fetch_page() -> str:
    with urllib.request.urlopen(TARGET_URL, timeout=5) as response:
        return response.read().decode("utf-8", errors="replace")


def send_alert(body: dict) -> None:
    request = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status >= 300:
            raise RuntimeError(f"Webhook returned HTTP {response.status}")


def main() -> None:
    already_alerted = False
    print(f"Monitoring {TARGET_URL}; sending events to {WEBHOOK_URL}", flush=True)
    while True:
        try:
            page = fetch_page()
            is_drifted = DRIFT_MARKER in page or EXPECTED_MARKER not in page
            if is_drifted and not already_alerted:
                event = {
                    "version": "1.0",
                    "status": "firing",
                    "severity": "error",
                    "alertname": "DemoServiceDrift",
                    "target": TARGET_NAME,
                    "instance": TARGET_URL,
                    "summary": "The demo Nginx page differs from its compliant baseline",
                    "description": "The disposable target contains a detected drift marker or is missing the expected baseline marker.",
                    "event_id": str(uuid.uuid4()),
                }
                send_alert(event)
                already_alerted = True
                print(f"Drift alert sent: {event['event_id']}", flush=True)
            elif not is_drifted and already_alerted:
                already_alerted = False
                print("Target is compliant again; monitor is re-armed.", flush=True)
        except (OSError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            print(f"Monitor check failed: {exc}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
