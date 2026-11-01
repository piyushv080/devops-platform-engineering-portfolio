import pytest

from app.services.log_processor import (
    analyze_logs,
    get_affected_servers,
    parse_log_line,
    read_log_file,
)

def test_parse_valid_log():
    log = "2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%"

    result = parse_log_line(log)

    assert result["level"] == "ERROR"
    assert result["server"] == "server-01"
    assert result["message"] == "Disk usage reached 95%"


def test_invalid_log_level_raises_value_error():
    log = "2026-10-31T09:15:22 DEBUG server-01 Disk warning"

    with pytest.raises(ValueError):
        parse_log_line(log)


def test_invalid_timestamp_raises_value_error():
    log = "INVALID_DATE ERROR server-01 Disk warning"

    with pytest.raises(
        ValueError,
        match="timestamp must be in ISO 8601 format",
    ):
        parse_log_line(log)


def test_read_log_file_with_mixed_records(tmp_path):
    log_file = tmp_path / "sample.log"
    log_file.write_text(
        "2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%\n"
        "INVALID LOG ENTRY\n"
        "2026-10-31T09:17:22 INFO server-03 Health check passed\n"
    )

    parsed_logs, invalid_logs = read_log_file(log_file)

    assert len(parsed_logs) == 2
    assert len(invalid_logs) == 1
    assert invalid_logs[0]["line"] == "INVALID LOG ENTRY"


def test_analyze_logs_counts_severity_levels():
    parsed_logs = [
        parse_log_line(
            "2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%"
        ),
        parse_log_line(
            "2026-10-31T09:16:22 ERROR server-02 Service stopped"
        ),
        parse_log_line(
            "2026-10-31T09:17:22 WARNING server-03 CPU usage reached 80%"
        ),
    ]

    counts = analyze_logs(parsed_logs)

    assert counts["ERROR"] == 2
    assert counts["WARNING"] == 1
    assert counts["INFO"] == 0


def test_get_affected_servers_returns_unique_servers_in_order():
    parsed_logs = [
        parse_log_line(
            "2026-10-31T09:15:22 ERROR server-01 Disk usage reached 95%"
        ),
        parse_log_line(
            "2026-10-31T09:16:22 WARNING server-02 CPU usage reached 80%"
        ),
        parse_log_line(
            "2026-10-31T09:17:22 INFO server-01 Health check passed"
        ),
        parse_log_line(
            "2026-10-31T09:18:22 ERROR server-03 Service stopped"
        ),
    ]

    servers = get_affected_servers(parsed_logs)

    assert len(servers) == 3
    assert servers.count("server-01") == 1
    assert servers == ["server-01", "server-02", "server-03"]
