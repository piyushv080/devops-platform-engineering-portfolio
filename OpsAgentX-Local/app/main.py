
from app.services.log_processor import (
    read_log_file,
    analyze_logs,
    get_affected_servers,
)


if __name__ == "__main__":

    logs, invalid_logs = read_log_file(
        "data/sample_logs_mixed.txt"
    )

    summary = analyze_logs(logs)
    servers = get_affected_servers(logs)

    print("\nOPSAGENTX - LOG ANALYSIS REPORT")
    print("-" * 40)

    print(f"Total logs: {len(logs) + len(invalid_logs)}")
    print(f"Valid logs: {len(logs)}")
    print(f"Invalid logs: {len(invalid_logs)}")

    for level, count in summary.items():
        print(f"{level}: {count}")

    print(f"Affected servers: {', '.join(servers)}")
