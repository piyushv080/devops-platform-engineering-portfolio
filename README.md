# DevOps Platform Engineering Portfolio

Hands-on projects exploring infrastructure automation, event-driven recovery,
operational reporting, and log analysis. The projects currently available in
the `dev` branch are listed below.

## Projects

### Event-Driven Remediation

An end-to-end lab that detects drift in a disposable Nginx service and routes an
approved alert through Prometheus, Alertmanager, and Ansible Rulebook to AWX.
AWX repairs and verifies the target, then records the incident outcome in
ServiceNow.

- **Technologies:** Docker Compose, Prometheus, Blackbox Exporter, Alertmanager,
  Ansible Rulebook, AWX, Ansible, and ServiceNow.
- **Guide:** [Event-Driven Remediation](event-driven-remediation/README.md)
- **Visual walkthrough:** [End-to-end guide](event-driven-remediation/END_TO_END_GUIDE.html)

### Healthcheck Automation

An AWX reporting project with three read-only reports: automation job health,
ServiceNow CMDB data quality, and repeated-work opportunities for automation.
It prints summaries in AWX and creates detailed HTML reports without changing
AWX or ServiceNow records.

- **Technologies:** Ansible, AWX, Python, Jinja, and ServiceNow APIs.
- **Guide:** [Healthcheck Automation](healthcheck-automation/README.md)

### OpsAgentX Local Log Analyzer

A small Python application that parses infrastructure log files, counts
`ERROR`, `WARNING`, and `INFO` records, lists affected servers, and keeps
malformed lines with their error reasons.

- **Technologies:** Python standard library and pytest.
- **Guide:** [OpsAgentX Local](OpsAgentX-Local/README.md)
- **Run locally:** from `OpsAgentX-Local/`, run `python -m app.main`.

## Validation workflow

The [event-lab GitHub Actions workflow](.github/workflows/validate-event-lab.yml)
runs for relevant pushes and pull requests targeting `dev`. It compiles the
project's Python files, runs mock-only unit tests, and checks the Ansible
playbook syntax.

## Getting started

Each project guide explains its prerequisites, configuration, and run steps.
Keep AWX, ServiceNow, and SSH credentials in the appropriate secret stores;
never commit credentials to this repository.
