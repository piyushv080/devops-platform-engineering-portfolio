# Event-Driven Remediation

An end-to-end lab that detects a web service drift, dispatches an approved event to AWX, repairs a disposable Nginx target, independently verifies recovery, and records the result in ServiceNow.

## Project guide

The complete project documentation, including its architecture, setup, test commands, restore workflow, and troubleshooting, is in [event-driven-remediation/README.md](event-driven-remediation/README.md).

The standalone visual walkthrough is [event-driven-remediation/END_TO_END_GUIDE.html](event-driven-remediation/END_TO_END_GUIDE.html).

## Main flow

1. Blackbox Exporter probes the disposable Nginx page.
2. Prometheus detects an unhealthy response or missing approved page marker.
3. Alertmanager sends the firing alert to Ansible Rulebook.
4. Rulebook validates the event and launches the AWX remediation template.
5. AWX records or reuses the correlated ServiceNow incident, restores the demo page over SSH, and independently checks the HTTP response.
6. AWX resolves the incident only after the healthy page is verified.

## Quick test

Run these commands from the `event-driven-remediation` directory:

```bash
ansible-playbook run_event_driven_automation.yml -e lab_environment_action=start
ansible-playbook run_event_driven_automation.yml -e lab_environment_action=drift
```

The drift action creates the alert condition. Keep the monitoring stack and event listener running, then watch the newest AWX job. To restore the healthy page manually:

```bash
ansible-playbook run_event_driven_automation.yml -e lab_environment_action=restore
```

## Technologies

Docker Compose · Prometheus · Blackbox Exporter · Alertmanager · Ansible Rulebook · AWX · Ansible · ServiceNow Table API

## Safety

Remediation is scoped to the disposable demo target and allow-listed alert. Keep controller tokens, ServiceNow credentials, and SSH private keys in their intended secret stores; never commit them.
