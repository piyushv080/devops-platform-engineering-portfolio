# DevOps Platform Engineering Portfolio

This portfolio presents practical platform engineering projects focused on
operational reliability, service automation, and useful engineering insights.
Each project has its own architecture, setup guide, and demo instructions.

## Projects

| Project | What it demonstrates | Main technologies |
|---|---|---|
| [Event-driven remediation](event-driven-remediation/README.md) | Detect a web-service issue, send an approved event to AWX, track work in ServiceNow, remediate the disposable service, and verify recovery. | Docker, Prometheus, Alertmanager, Ansible Rulebook, AWX, ServiceNow |
| [Healthcheck automation](healthcheck-automation/README.md) | Produce read-only reports on AWX job health, ServiceNow CMDB quality, and repeated work that may be suitable for automation. | Ansible, AWX, ServiceNow, Jinja2 |

## Repository structure

```text
devops-platform-engineering-portfolio/
├── README.md
├── ansible.cfg
├── event-driven-remediation/
└── healthcheck-automation/
```

The root `ansible.cfg` lets AWX resolve roles stored inside either project
when the portfolio repository is configured as one AWX Project.
