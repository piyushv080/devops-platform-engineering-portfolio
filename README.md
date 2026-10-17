# DevOps Platform Engineering Portfolio

This repository is a growing portfolio of practical DevOps and platform engineering projects. Each project demonstrates an end-to-end workflow, the tools used, and instructions for running or understanding the demo. Additional projects will be added as they are completed.

## Current project

### Event-Driven Remediation

**Project folder:** [`event-driven-remediation/`](event-driven-remediation/)

This completed project demonstrates how Prometheus detects drift in a disposable Nginx service, Alertmanager delivers an event to Ansible Rulebook, and AWX runs a controlled repair. The playbook verifies recovery and records the incident outcome in ServiceNow.

Start with the [project README](event-driven-remediation/README.md) for setup and testing instructions. The [end-to-end HTML guide](event-driven-remediation/END_TO_END_GUIDE.html) gives a visual walkthrough of the architecture and test flow.

## Repository layout

```text
README.md
ansible.cfg
event-driven-remediation/
```

New project folders and their guides can be added here as the portfolio grows.
