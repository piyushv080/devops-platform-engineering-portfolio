# Event-driven incident remediation lab

This project demonstrates event-driven incident remediation using a monitoring webhook, an Ansible Rulebook listener, AWX, a disposable Nginx target, and a ServiceNow developer instance. An alert starts a job that records an incident, repairs the target, verifies recovery, and updates the incident.

## Flow

```mermaid
flowchart LR
    subgraph Sources[Event sources]
        MON[Demo monitor in WSL]
        EXT[External monitoring platform]
    end

    subgraph Lab[Local disposable lab]
        TARGET[Demo Nginx container<br/>HTTP 8081 · SSH 2222]
    end

    subgraph EDA[Event listener in WSL]
        WEBHOOK[ansible-rulebook webhook<br/>POST /endpoint · port 5000]
        RULE{Rule matches<br/>error + firing + required fields}
    end

    subgraph AWX[AWX on Kubernetes]
        API[AWX Controller API]
        JT[Incident Remediation<br/>Job Template]
        EE[AWX execution environment]
        PROJECT[Synced Git project<br/>playbook + inventory]
    end

    SN[ServiceNow PDI<br/>Incident Table API]

    MON -->|poll HTTP 8081| TARGET
    MON -->|drift alert JSON| WEBHOOK
    EXT -->|mapped alert JSON| WEBHOOK
    WEBHOOK --> RULE
    RULE -->|matched event + AWX token| API
    API -->|launch with event data| JT
    PROJECT -. provides playbook .-> JT
    JT --> EE
    EE -->|find or create incident;<br/>write detection work note| SN
    EE -->|SSH repair on port 2222| TARGET
    EE -->|HTTP recovery check on port 8081| TARGET
    EE -->|verified: resolve + work notes| SN
    EE -->|repair/check failed: leave open + note| SN

```

The demo monitor polls the disposable Nginx page and posts an alert when it detects drift. A real monitoring product can replace it by posting a mapped alert to the same webhook. The rulebook listener matches the alert and launches the AWX job through the Controller API. The playbook validates and allow-lists the target, records the incident before remediation, then resolves it only after the repaired page passes an HTTP check. If repair or verification fails, it records the failure and leaves the incident open.

## Video walkthrough: 2–3 minutes

Keep the video focused on the event-to-recovery flow. AWX is the automation engine in this story; the repository and platform setup that hosts AWX do not need a separate explanation.

### Prepare the demo

1. Start the disposable target and confirm the compliant page is available:

   ```bash
   cd ~/pivanta.org/event-driven-remediation
   docker compose up -d
   curl -fsS http://localhost:8081/ | grep 'Pivanta Event Remediation Demo - compliant'
   ```

2. Start the Rulebook webhook listener by following [Run the event listener](#3-run-the-event-listener). Keep that terminal open.
3. Open `http://localhost:8081/`, the AWX Job Template and recent job output, and the ServiceNow incident list in your browser. Arrange the windows so you can switch between them quickly.
4. Start the monitor in another terminal:

   ```bash
   cd ~/pivanta.org/event-driven-remediation
   source .venv/bin/activate
   python monitor/demo_monitor.py
   ```

5. Start your screen recorder. Hide terminals that contain tokens or credential values. Avoid showing credential forms or private-key files.

### Record the successful event

1. Show the architecture diagram above and briefly trace the arrows from monitor to incident and back to the recovered service.
2. Introduce reversible drift in the disposable target:

   ```bash
   bash scripts/introduce-drift.sh
   ```

3. Show the monitor log reporting a drift alert. Switch to AWX and show the automatically launched `Incident Remediation - Demo Nginx` job.
4. In the job output, show the key stages: alert validation, incident lookup/create, detection work note, SSH page repair, independent HTTP check, and incident resolution.
5. Show the restored page at `http://localhost:8081/` and the ServiceNow incident work notes/resolution information.
6. End with the outcome: the alert triggered the workflow, the service was verified healthy, and the incident records the result.

### Narration script

Read this while showing the corresponding screen. The timing is a guide; pause briefly between screens.

| Time | Show | Narration |
|---|---|---|
| 0:00–0:20 | Architecture diagram | “This is an event-driven remediation lab. A monitor watches a disposable web service. When it detects drift, it sends an alert to an Ansible Rulebook webhook. A matching event launches an AWX job, which coordinates the repair and incident update.” |
| 0:20–0:40 | Compliant page, then run `introduce-drift.sh` | “The Nginx container starts with a known-good page. I’m introducing a small, reversible change to simulate a service problem. The monitor detects that the expected page content is missing and sends an error event.” |
| 0:40–1:00 | Monitor output, Rulebook listener, AWX job | “The rulebook accepts firing error alerts for the allowed demo target and passes the event to AWX. The job validates the event again and looks for an active incident correlated to this alert, which helps avoid duplicate incidents.” |
| 1:00–1:25 | AWX output and ServiceNow work notes | “AWX creates or reuses the ServiceNow incident and records a detection note before changing the target. That gives the response an incident record and an audit trail.” |
| 1:25–1:50 | AWX repair and verification tasks | “The job connects to the disposable target over SSH, restores the known-good page, and then checks the service independently over HTTP. The incident is resolved only after that verification passes.” |
| 1:50–2:10 | ServiceNow incident and restored page | “Here the page is healthy again, and the incident contains the remediation result. If the repair or verification had failed, the workflow would add a failure note and leave the incident open.” |
| 2:10–2:20 | Architecture diagram or title card | “That’s the complete event-to-recovery loop: detect, create an incident, remediate, verify, and report the outcome.” |

For a clean recording, use a successful completed run and trim setup delays. If the live run takes too long, record the architecture first, then use the completed AWX job and incident as the result screens.

## Components

- `target/`: disposable Nginx + SSH container. The only remediation target in this lab.
- `monitor/`: small standard-library Python poller that emits an alert when the page contains the drift marker.
- `rulebooks/monitoring-alerts.yml`: webhook source and rule that launches the AWX job.
- `playbooks/remediate_demo_alert.yml`: creates/correlates a ServiceNow incident, restores the demo page, checks recovery, and updates incident work notes/state.
- `inventory/hosts.yml`: example AWX inventory for the container SSH endpoint.
- `samples/error-alert.json`: event body for testing the listener without waiting for the monitor.
- `scripts/`: helper to create a lab SSH key and a script that introduces reversible demo drift.

## Requirements

- Docker Desktop with Kubernetes enabled; AWX running from `enterprise-ops-orchestrator/`.
- Python 3.9+ and Java JDK 17+ in WSL, plus `ansible-rulebook`, Ansible, `ansible-runner`, and the `ansible.eda` collection.
- An AWX API token and an AWX machine credential for the disposable container.
- For incident creation, a ServiceNow PDI and a least-privilege API user configured in an AWX custom credential. Never place tokens, passwords, or private keys in Git.

## 1. Build and start the isolated target

In WSL:

```bash
cd ~/pivanta.org/event-driven-remediation
bash scripts/prepare-lab-key.sh
docker compose up --build -d
```

Import `secrets/ansible_ed25519` into an AWX Machine credential. The helper creates `secrets/`, which is ignored by Git. In AWX, create an inventory with the example host in `inventory/hosts.yml`, or copy its variables into the AWX inventory. The target address is `host.docker.internal:2222`; verify reachability from an AWX job before proceeding. The disposable web page is available at `http://localhost:8081` from WSL.

The target SSH account has passwordless sudo inside this disposable container to allow Ansible to replace the demo page. Do not reuse this image or credential on a real host.

## 2. Configure AWX

Use the AWX instance deployed by `enterprise-ops-orchestrator`, but create a **new AWX Project** for this lab. The existing AWX Project named `enterprise-ops-orchestrator` syncs the GitHub repository of the same name on branch `dev`; it cannot see this sibling folder on your WSL disk. `AWX GitOps Configuration` is for controller configuration and should not be used as the lab playbook Project.

To preserve this folder as its own project, publish its contents to a Git repository AWX can sync, then create a new Project in the same AWX organization. The recommended branch for this lab is `dev`; set the AWX Project SCM branch to `dev` and attach a GitHub SCM credential that has read access to this repository. If this repository's root contains the contents of this folder, choose `playbooks/remediate_demo_alert.yml` as the playbook. If you instead commit this directory under `event-driven-remediation/` inside the existing `enterprise-ops-orchestrator` GitHub repository, sync that existing Project and choose `event-driven-remediation/playbooks/remediate_demo_alert.yml`.

Create a job template:

- Name: `Incident Remediation - Demo Nginx`
- Playbook: the path relative to the synced repository root (see above)
- Inventory: the one-host disposable lab inventory
- Machine credential: the key generated above, with privilege escalation enabled
- Variables: enable **Prompt on launch** for extra variables so `ansible_eda.event` can be supplied.

For ServiceNow, create an AWX custom credential type with these fields:

```yaml
fields:
  - id: instance_url
    type: string
    label: ServiceNow instance URL
  - id: username
    type: string
    label: API username
  - id: password
    type: string
    label: API password
    secret: true
required: [instance_url, username, password]
```

Set its environment injector to:

```yaml
env:
  SNOW_INSTANCE_URL: '{{ instance_url }}'
  SNOW_USERNAME: '{{ username }}'
  SNOW_PASSWORD: '{{ password }}'
```

Create a credential of that type using your PDI URL and integration account, then attach it to the job template. The playbook uses the ServiceNow Table API at `/api/now/table/incident`; confirm your PDI's field choices and allowed incident state values before using it.

The job only accepts alerts whose `target` equals `demo-nginx`. This is an allow-list, not a general remote-host remediation mechanism.

## 3. Run the event listener

Install the dependencies in a dedicated virtual environment. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ansible ansible-rulebook ansible-runner
ansible-galaxy collection install -r requirements.yml
```

On Ubuntu/WSL, install Java and Python's venv support first if needed: `sudo apt install openjdk-17-jdk python3-venv python3-pip`. Current Rulebook installation requires Java 17 or newer ([official installation guide](https://docs.ansible.com/projects/rulebook/en/latest/installation.html)).

Create an AWX API token in AWX. In the same WSL shell, export it (do not commit it) and run:

```bash
export AWX_TOKEN='paste-token-here'
ansible-rulebook \
  --inventory localhost, \
  --rulebook rulebooks/monitoring-alerts.yml \
  --controller-url http://127.0.0.1:8080/api/v2 \
  --controller-token "$AWX_TOKEN"
```

Keep the AWX port-forward from `./start-awx.sh` running in another terminal. The webhook listener binds to port 5000 and is unauthenticated for this local-only demo. Do not expose it to the internet.

## 4. Exercise the event flow

Open a second WSL terminal. First introduce reversible drift into the disposable container:

```bash
bash scripts/introduce-drift.sh
```

Run the monitor in another terminal:

```bash
python monitor/demo_monitor.py
```

Or post the sample event directly to test the rule without the monitor:

```bash
curl -X POST http://127.0.0.1:5000/endpoint \
  -H 'Content-Type: application/json' \
  --data @samples/error-alert.json
```

The expected event keys are `payload.severity`, `payload.status`, `payload.target`, `payload.alertname`, and `payload.event_id`. The rule matches `severity: error` and `status: firing`; it passes the event to AWX, where the playbook validates it again.

## 5. ServiceNow behavior

The playbook reuses an active incident by `dedup_key` (or the `alertname:target` fallback) before creating one, writes the AWX remediation result to work notes, and only requests resolution after the target responds with the expected page content. On repair/verification failure it records the failure and leaves the incident open. A real monitoring source should provide a stable deduplication key for an alert episode. ServiceNow field availability, API ACLs, and state/close-code values can differ by PDI configuration, so validate these against your instance.

If ServiceNow credentials are not attached, the job fails before making target changes. This avoids silently remediating without the requested incident audit trail.

## 6. AWX schedule and real monitoring integration

An AWX schedule runs periodic jobs; it is not a persistent event listener. This repository includes `playbooks/audit_and_emit_event.yml` for periodic polling. Create a second AWX job template named `Scheduled Demo Baseline Audit`, select `playbooks/audit_and_emit_event.yml`, and use an inventory that permits the localhost play. From the template's **Schedules** tab, add a schedule such as every five minutes. The AWX execution environment must be able to reach `host.docker.internal:8081` and the Rulebook listener at `host.docker.internal:5000`; verify those routes from an AWX job before relying on the schedule.

For event-based operation, keep `ansible-rulebook` running as a managed process/service and configure the monitoring tool to POST alerts to its `/endpoint`. A production monitoring tool can send to the same webhook after its payload is mapped to the expected fields. Use a protected, managed Event-Driven Ansible environment or service for a persistent listener; this unauthenticated local webhook is for the isolated demo only.

## Operations and cleanup

- Stop the demo monitor with Ctrl+C and the rulebook listener with Ctrl+C.
- Stop/remove only the disposable target with `docker compose down` from this folder.
- Do not run cleanup against the AWX namespace for routine lab shutdown.
- Rotate the AWX token and PDI password if they are accidentally exposed.

## Important platform note

This is community AWX plus a separately run `ansible-rulebook` listener, not the Red Hat Ansible Automation Platform Event-Driven Ansible Controller. Rulebook's `run_job_template` action needs a Controller API URL/token; the AWX job template must allow launch-time variables. See [Rulebook actions](https://docs.ansible.com/projects/rulebook/en/latest/actions.html#run-job-template), [event sources](https://ansible.readthedocs.io/projects/rulebook/en/stable/sources.html), and [AWX job templates](https://docs.ansible.com/projects/awx/en/24.6.1/quickstart/create_job.html).
