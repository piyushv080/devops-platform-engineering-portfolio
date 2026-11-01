
from datetime import datetime

SUPPORTED_LEVELS = {"ERROR", "WARNING", "INFO"}


def parse_log_line(log_line):
    """Convert a raw infrastructure log into structured data."""

    if not isinstance(log_line, str):
        raise ValueError("log line must be a string")

    fields = log_line.split(maxsplit=3)

    if len(fields) != 4:
        raise ValueError(
            "log line must contain timestamp, level, server and message"
        )

    timestamp, level, server, message = fields

    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError(
            "timestamp must be in ISO 8601 format"
        ) from exc

    if level not in SUPPORTED_LEVELS:
        raise ValueError(f"unsupported log level: {level}")

    if not server.strip():
        raise ValueError("server name cannot be empty")

    if not message.strip():
        raise ValueError("message cannot be empty")

    return {
        "timestamp": timestamp,
        "level": level,
        "server": server,
        "message": message,
    }


def read_log_file(file_path):
    """Return parsed records and invalid records."""

    parsed_logs = []
    invalid_logs = []

    with open(file_path, "r") as log_file:
        for line in log_file:
            stripped_line = line.strip()

            try:
                parsed_logs.append(parse_log_line(stripped_line))

            except ValueError as exc:
                invalid_logs.append({
                    "line": stripped_line,
                    "error": str(exc),
                })

    return parsed_logs, invalid_logs


def analyze_logs(parsed_logs):
    """Count log records by severity level."""

    counts = {level: 0 for level in SUPPORTED_LEVELS}

    for log in parsed_logs:
        counts[log["level"]] += 1

    return counts


def get_affected_servers(parsed_logs):
    """Return unique server names in their original order."""

    servers = []
    seen_servers = set()

    for log in parsed_logs:
        server = log["server"]

        if server not in seen_servers:
            seen_servers.add(server)
            servers.append(server)

    return servers
