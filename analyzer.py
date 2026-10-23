
import argparse
import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LOG = BASE_DIR / "logs" / "application.log"
DEFAULT_REPORT = BASE_DIR / "reports" / "log_summary.csv"

LOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"(INFO|WARNING|ERROR) (.+)$"
)


def read_logs(file_path):
    """Read and parse valid application log entries."""
    records = []
    invalid_lines = 0

    with file_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            match = LOG_PATTERN.match(line)

            if not match:
                invalid_lines += 1
                continue

            timestamp_text, level, message = match.groups()

            try:
                timestamp = datetime.strptime(
                    timestamp_text, "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                invalid_lines += 1
                continue

            records.append({
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "line_number": line_number
            })

    return records, invalid_lines


def filter_logs(records, level=None, keyword=None, date=None):
    """Filter records by severity, keyword, and date."""
    filtered = []

    for record in records:
        if level and record["level"] != level:
            continue

        if keyword and keyword.lower() not in record["message"].lower():
            continue

        if date and record["timestamp"].date().isoformat() != date:
            continue

        filtered.append(record)

    return filtered


def display_summary(records):
    """Print severity totals and most frequent error messages."""
    print("\nLOG SUMMARY")
    print("-" * 35)

    severity_counts = Counter(
        record["level"] for record in records
    )

    for level in ("INFO", "WARNING", "ERROR"):
        print(f"{level}: {severity_counts[level]}")

    print(f"Total valid events: {len(records)}")

    error_counts = Counter(
        record["message"]
        for record in records
        if record["level"] == "ERROR"
    )

    print("\nMOST FREQUENT ERRORS")
    print("-" * 35)

    if not error_counts:
        print("No errors found.")
    else:
        for message, count in error_counts.most_common():
            print(f"{message}: {count}")


def display_records(records):
    """Display matching log entries."""
    print("\nMATCHING LOG ENTRIES")
    print("-" * 60)

    if not records:
        print("No matching entries found.")
        return

    for record in records:
        timestamp = record["timestamp"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(f"{timestamp} {record['level']} {record['message']}")


def export_csv(records, report_path):
    """Export matching records to a CSV file."""
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["timestamp", "level", "message", "line_number"]
        )
        writer.writeheader()

        for record in records:
            writer.writerow({
                "timestamp": record["timestamp"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "level": record["level"],
                "message": record["message"],
                "line_number": record["line_number"]
            })

    print(f"\nCSV report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="LogLens: Application Log Analyzer"
    )

    parser.add_argument(
        "--file",
        default=str(DEFAULT_LOG),
        help="Path to the application log file"
    )

    parser.add_argument(
        "--level",
        choices=["INFO", "WARNING", "ERROR"],
        help="Filter by severity level"
    )

    parser.add_argument(
        "--keyword",
        help="Search for text in log messages"
    )

    parser.add_argument(
        "--date",
        help="Filter by date in YYYY-MM-DD format"
    )

    parser.add_argument(
        "--export",
        nargs="?",
        const=str(DEFAULT_REPORT),
        help="Export matching records to CSV"
    )

    args = parser.parse_args()

    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            parser.error("--date must use YYYY-MM-DD format")

    log_path = Path(args.file)

    if not log_path.is_absolute():
        log_path = Path.cwd() / log_path

    if not log_path.is_file():
        parser.error(f"Log file not found: {log_path}")

    try:
        records, invalid_lines = read_logs(log_path)
    except (OSError, UnicodeError) as error:
        parser.error(f"Could not read log file: {error}")

    matching_records = filter_logs(
        records,
        level=args.level,
        keyword=args.keyword,
        date=args.date
    )

    print("LOGLENS - APPLICATION LOG ANALYZER")
    print("=" * 40)
    print(f"Log file: {log_path}")
    print(f"Valid entries: {len(records)}")
    print(f"Invalid non-empty lines skipped: {invalid_lines}")
    print(f"Matching entries: {len(matching_records)}")

    display_records(matching_records)
    display_summary(matching_records)

    if args.export is not None:
        report_path = Path(args.export)

        if not report_path.is_absolute():
            report_path = Path.cwd() / report_path

        try:
            export_csv(matching_records, report_path)
        except OSError as error:
            parser.error(f"Could not write CSV report: {error}")


if __name__ == "__main__":
    main()
