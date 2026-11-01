# Log Analyzer

A small Python learning project that reads infrastructure log files, validates
each record, counts records by severity, and lists the affected servers. Valid
records are kept even when another line in the same file is malformed; rejected
lines are returned with the reason they were rejected.

## Log format

Each valid line has four fields:

```text
<ISO-style timestamp> <level> <server> <message>
```

Supported levels are `ERROR`, `WARNING`, and `INFO`. The message may contain
spaces. For example:

```text
2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%
```

The parser uses `datetime.fromisoformat()` to validate the timestamp. That
accepts supported ISO-style formats; it does not enforce one exact timestamp
spelling.

## Project files

```text
app/
  main.py                 Application functions and command-line report
  00_backend.py           Learning copy of the parsing and analysis functions
data/
  sample_logs.txt         All-valid example log file
  sample_logs_mixed.txt   Example with valid and invalid records
tests/
  test_log_processor.py   Six pytest tests
```

Use `app.main` as the application module. `00_backend.py` is kept as a learning
reference; the leading digits make it unsuitable for a normal Python import.

## Run the analyzer

From the project root, run:

```bash
python -m app.main
```

The analyzer uses only the Python standard library. To run its tests, install
pytest if it is not already available:

```bash
python -m pip install pytest
```

The example reads `data/sample_logs_mixed.txt`. It contains five lines: three
valid records and two invalid records. The report includes total, valid, and
invalid counts, severity counts, and the unique servers in first-seen order.
The expected counts are:

```text
Total logs: 5
Valid logs: 3
Invalid logs: 2
ERROR: 1
WARNING: 1
INFO: 1
```

The two rejected records are retained with their original text and an error
message. For example:

```python
[
    {
        "line": "INVALID LOG ENTRY",
        "error": "log line must contain timestamp, level, server and message",
    },
    {
        "line": "2026-10-31T09:18:22 DEBUG server-04 Unsupported severity",
        "error": "unsupported log level: DEBUG",
    },
]
```

## Use the functions

`parse_log_line()` turns one valid line into a dictionary:

```python
from app.main import parse_log_line

record = parse_log_line(
    "2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%"
)
print(record["server"])  # server-01
```

`read_log_file()` returns two lists as a tuple. The first contains parsed
records; the second contains rejected records and their error reasons:

```python
from app.main import read_log_file

parsed_logs, invalid_logs = read_log_file("data/sample_logs_mixed.txt")
```

Pass parsed records to the analysis helpers:

```python
from app.main import analyze_logs, get_affected_servers

severity_counts = analyze_logs(parsed_logs)
servers = get_affected_servers(parsed_logs)
```

`analyze_logs()` returns a dictionary with `ERROR`, `WARNING`, and `INFO`
counts. `get_affected_servers()` returns unique server names while preserving
their first-seen order.

## Python concepts practiced

| Python concept | Where it is used |
| --- | --- |
| Variables | Store parsed records, invalid records, and counts. |
| Strings | Represent and process raw log lines and messages. |
| Functions | Divide parsing, file reading, counting, and server detection into reusable steps. |
| Conditions (`if`) | Validate input type, field count, timestamp, level, server, and message. |
| Loops (`for`) | Read and process each log line and parsed record. |
| Lists | Store parsed logs, invalid logs, and the ordered server results. |
| Dictionaries | Represent structured log records and severity counts. |
| Sets | Track seen servers so duplicates are excluded. |
| Dictionary comprehension | Initialize a zero count for each supported severity. |
| Exception handling | Raise `ValueError` for invalid records and capture each error in `read_log_file()`. |
| File handling | Use `with open(..., "r")` to read the log file and close it automatically. |
| Tuple unpacking | Separate the two lists returned by `read_log_file()`. |
| Imports | Import `datetime` and reuse application functions from `app.main` in tests. |
| Pytest | Automatically check valid behavior and expected failures. |

The parser raises `ValueError` when a line is invalid. The file reader catches
that error around each individual line, allowing later records to be processed.
File access errors, such as a missing file, are not treated as malformed log
records and will still be reported to the caller.

## Tests

Run the test suite from the project root:

```bash
python -m pytest -v
```

The suite contains six tests, reported as **6/6 passing**:

| Test | What it verifies |
| --- | --- |
| `test_parse_valid_log` | Parses a valid log line. |
| `test_invalid_log_level_raises_value_error` | Rejects an unsupported severity. |
| `test_invalid_timestamp_raises_value_error` | Rejects an invalid timestamp and checks the error message. |
| `test_read_log_file_with_mixed_records` | Processes valid and invalid file lines and retains the invalid line. |
| `test_analyze_logs_counts_severity_levels` | Counts `ERROR`, `WARNING`, and `INFO` records. |
| `test_get_affected_servers_returns_unique_servers_in_order` | Removes duplicate servers and preserves first-seen order. |

The tests use `pytest.raises()` to verify expected failures. Its `match`
argument can also check that the exception message contains expected text.
