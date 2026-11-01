# OpsAgentX Local

## 1. Project Overview

OpsAgentX is an AI-powered infrastructure incident diagnosis and controlled remediation platform.

The long-term objective is to build a system that can:

1. Receive infrastructure incidents from monitoring tools or ServiceNow.
2. Collect and analyze infrastructure logs.
3. Identify affected servers and services.
4. Use an AI model to investigate the incident.
5. Retrieve relevant runbooks and historical incidents.
6. Recommend a remediation action.
7. Validate the proposed action against security policies.
8. Request human approval.
9. Execute approved remediation through Ansible.
10. Verify the result and maintain an audit history.

This local implementation uses Python and will gradually integrate Ollama, FastAPI, databases, and Ansible.

**Important:** The initial development environment uses sample data and simulated remediation. No production infrastructure actions are permitted.

---

## 2. Why Are We Building This Project?

The purpose is not simply to create an AI chatbot.

The purpose is to learn how to engineer a complete application.

This project will help develop skills in:

- Python programming and software design
- Modular application architecture
- API development
- Data validation
- Exception handling
- Automated testing
- Database integration
- LLM integration
- AI agents and tool calling
- Workflow orchestration
- Infrastructure automation
- Security and auditability

The project will be developed incrementally. Each component must work and be tested before introducing the next layer.

---

## 3. Current Project Status

### Completed: Infrastructure Log Analyzer

The first milestone is a Python-based log analyzer.

It can:

- Read a log file.
- Parse individual log records.
- Validate timestamps.
- Validate severity levels.
- Identify malformed log entries.
- Count ERROR, WARNING and INFO records.
- Identify unique affected servers.
- Generate a basic analysis report.

### Sample Input

```text
2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%
2026-10-31T09:16:22 WARNING server-02 CPU usage reached 80%
2026-10-31T09:17:22 INFO server-03 Health check passed
```

### Expected Output

```text
OPSAGENTX - LOG ANALYSIS REPORT
----------------------------------------
Total logs: 5
Valid logs: 3
Invalid logs: 2
ERROR: 1
WARNING: 1
INFO: 1
Affected servers: server-01, server-03, server-02
```

The sample mixed log file also contains two invalid records, which are retained separately rather than crashing the application.

---

## 4. Current Architecture

```text
OpsAgentX-Local/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   └── services/
│       ├── __init__.py
│       └── log_processor.py
│
├── data/
│   ├── sample_logs.txt
│   └── sample_logs_mixed.txt
│
├── reports/
│
├── tests/
│   ├── __init__.py
│   └── test_log_processor.py
│
├── 001log_analyzer/
│   └── Personal Python learning archive
│
├── .venv/
├── pytest.ini
├── requirements.txt
└── README.md
```

The `001log_analyzer` directory is a personal learning archive and should not be committed to GitHub.

### Module responsibilities

**app/main.py**

The application entry point.

Responsibilities:

- Import required functions.
- Call the log-processing service.
- Display the analysis report.

It should not contain all the business logic.

**app/services/log_processor.py**

Contains the log-processing business logic:

- `parse_log_line()`
- `read_log_file()`
- `analyze_logs()`
- `get_affected_servers()`

**tests/test_log_processor.py**

Contains automated tests that verify the behaviour of the log-processing functions.

---

## 5. Understanding the Core Functions

### 5.1 parse_log_line()

Purpose: Convert one raw log string into a structured Python dictionary.

Input:

```python
log = "2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%"
```

Output:

```python
{
    "timestamp": "2026-10-31T09:15:22",
    "level": "ERROR",
    "server": "server-01",
    "message": "Disk usage reached 95%"
}
```

Concepts used:

- Strings
- String splitting
- Variables
- Conditions
- Functions
- Dictionaries
- Exception handling
- Timestamp validation

### 5.2 read_log_file()

Purpose: Read a file and process its log records.

It separates:

- Valid log records
- Invalid log records

Concepts used:

- File handling
- Loops
- Lists
- Function calls
- Exception handling
- Tuple return values

### 5.3 analyze_logs()

Purpose: Calculate how many logs belong to each severity level.

Example:

```python
{
    "ERROR": 2,
    "WARNING": 1,
    "INFO": 0
}
```

Concepts used:

- Dictionaries
- Dictionary comprehensions
- Loops
- Data aggregation

### 5.4 get_affected_servers()

Purpose: Identify unique server names without duplicates.

Example:

```python
["server-01", "server-02", "server-03"]
```

Concepts used:

- Lists
- Sets
- Membership checks
- Loops
- Preserving insertion order

---

## 6. Why Did We Separate main.py and log_processor.py?

Initially, all the functions were inside `main.py`.

As an application grows, keeping every function in one file becomes difficult to maintain.

We separated the code based on responsibility.

Before:

```text
main.py
├── Parse logs
├── Read files
├── Validate records
├── Analyze severity
├── Find affected servers
└── Print report
```

After:

```text
main.py
└── Calls the application services

services/log_processor.py
├── Parse logs
├── Read files
├── Validate records
├── Analyze severity
└── Find affected servers
```

This is an example of separation of concerns.

The entry point coordinates the application. The service module performs the actual work.

Later, the same log-processing functions can be reused by:

- A FastAPI endpoint
- A Streamlit dashboard
- An AI diagnosis engine
- An automated incident workflow

---

## 7. Automated Testing with Pytest

We created six automated tests.

| Test | Purpose |
|---|---|
| `test_parse_valid_log` | Verifies valid log parsing |
| `test_invalid_log_level_raises_value_error` | Verifies severity validation |
| `test_invalid_timestamp_raises_value_error` | Verifies timestamp validation |
| `test_read_log_file_with_mixed_records` | Verifies valid and invalid record separation |
| `test_analyze_logs_counts_severity_levels` | Verifies severity aggregation |
| `test_get_affected_servers_returns_unique_servers_in_order` | Verifies unique server detection |

Run tests:

```bash
pytest -v
```

Latest verified result:

```text
6 passed in 0.02s
```

The tests verify the six behaviours above. They do not yet establish production readiness.

### Why automated testing matters

Suppose we change the log-processing logic.

Without tests, we would have to manually check every behaviour.

With pytest, we can execute the test suite after every change and detect regressions.

---

## 8. Development Environment

Operating environment:

- Windows
- WSL 2 Ubuntu
- Python 3.12.3
- pytest 9.2.0
- Dedicated Python virtual environment

### Activate virtual environment

```bash
source .venv/bin/activate
```

### Verify Python

```bash
python --version
which python
```

### Run application

```bash
python -m app.main
```

### Run tests

```bash
pytest -v
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## 9. Important Python Concepts Learned

| Concept | Application |
|---|---|
| Variables | Store log and incident data |
| Strings | Process raw log records |
| Functions | Create reusable operations |
| Conditions | Validate log records |
| Loops | Process multiple records |
| Lists | Store parsed logs |
| Dictionaries | Represent structured records |
| Sets | Identify unique servers |
| Dictionary comprehensions | Calculate severity counts |
| Exception handling | Handle invalid records |
| File handling | Read log files |
| Tuple unpacking | Receive multiple return values |
| Imports | Reuse functions across modules |
| Modules and packages | Organize application code |
| Pytest | Automate verification |

---

## 10. Future Development Roadmap

### Phase 1: Python Engineering

- Complete modular programming.
- Learn logging.
- Learn configuration management.
- Learn object-oriented programming.
- Learn type hints.
- Learn Pydantic.
- Improve automated testing.

Deliverable: A well-structured and tested log-processing application.

### Phase 2: Backend and APIs

- Learn HTTP and REST APIs.
- Build an incident ingestion API using FastAPI.
- Validate incoming incident payloads.
- Implement structured responses.
- Store incidents in SQLite or PostgreSQL.

Deliverable: Incident Management API.

### Phase 3: AI Integration

- Install and configure Ollama.
- Learn LLM APIs.
- Send structured incident data to an LLM.
- Generate structured diagnosis results.
- Validate AI responses using Pydantic.
- Handle timeouts and invalid responses.

Deliverable: AI Incident Analysis Engine.

### Phase 4: AI Agents

- Understand tools and function calling.
- Introduce LangChain.
- Introduce LangGraph.
- Build controlled diagnostic tools.
- Retrieve runbooks and historical incidents.

Deliverable: Infrastructure Diagnosis Agent.

### Phase 5: Controlled Remediation

- Define remediation policies.
- Implement allowlisted actions.
- Add human approval.
- Integrate Ansible.
- Simulate execution.
- Verify remediation results.
- Maintain audit history.

Deliverable: Controlled Remediation Workflow.

### Phase 6: Complete OpsAgentX

- Integrate all components.
- Build a dashboard.
- Add authentication and authorization.
- Add observability.
- Improve security and testing.
- Document deployment and operations.

Deliverable: Complete local OpsAgentX application.

---

## 11. Engineering Principles

These principles must guide future development:

1. Keep business logic separate from application entry points.
2. Write reusable functions.
3. Validate external input.
4. Handle errors explicitly.
5. Write tests for important behaviours.
6. Never trust raw LLM output.
7. Never provide unrestricted shell access to an AI agent.
8. Require policy validation and human approval for remediation.
9. Maintain an audit trail.
10. Verify the result of every remediation action.

---

## 12. Current Development Objective

The current objective is to finish the Python engineering foundation.

Do not rush into AI agents before understanding the underlying Python application.

The goal is to become capable of independently designing, implementing, testing, debugging and maintaining the components that will eventually make up OpsAgentX.

**Current milestone: Infrastructure Log Analyzer — completed with six passing tests.**