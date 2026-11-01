"""Learning file for log parsing, file reading, and analysis functions."""

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
    """Return parsed records and raw lines that could not be parsed."""
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
    """Return unique server names in the order they first appear."""
    servers = []
    seen_servers = set()

    for log in parsed_logs:
        server = log["server"]
        if server not in seen_servers:
            seen_servers.add(server)
            servers.append(server)

    return servers


# logs = read_log_file("data/sample_logs.txt")

# print(logs)
# print(f"Total logs: {len(logs)}")
# print(analyze_logs(logs))

# logs = read_log_file("data/sample_logs.txt")

# summary = analyze_logs(logs)

# print(summary)
# print(get_affected_servers(logs))

if __name__ == "__main__":
    logs, invalid_logs = read_log_file("data/sample_logs_mixed.txt")

    summary = analyze_logs(logs)
    servers = get_affected_servers(logs)

    print("\nOPSAGENTX - LOG ANALYSIS REPORT")
    print("-" * 40)

    print(f"Total logs: {len(logs)}")
    print(f"Valid logs: {len(logs)}")
    print(f"Invalid logs: {len(invalid_logs)}")

    for level, count in summary.items():
        print(f"{level}: {count}")

    print(f"Affected servers: {', '.join(servers)}")
