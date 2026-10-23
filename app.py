import csv
import io
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from analyzer import DEFAULT_LOG, filter_logs, read_logs


SEVERITIES = {"INFO", "WARNING", "ERROR"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_KEYWORD_LENGTH = 200

app = Flask(__name__)
app.config["LOG_FILE"] = DEFAULT_LOG


def _get_filters():
    severity = request.args.get("severity", "").strip()
    keyword = request.args.get("keyword", "").strip()
    date = request.args.get("date", "").strip()

    if severity and severity not in SEVERITIES:
        return None, ("severity must be INFO, WARNING, or ERROR", 400)

    if len(keyword) > MAX_KEYWORD_LENGTH:
        return None, (f"keyword must be at most {MAX_KEYWORD_LENGTH} characters", 400)

    if date:
        if not DATE_PATTERN.fullmatch(date):
            return None, ("date must use YYYY-MM-DD format", 400)
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return None, ("date must be a valid calendar date", 400)

    return {"severity": severity or None, "keyword": keyword or None, "date": date or None}, None


def _load_filtered_records(filters):
    log_file = Path(app.config["LOG_FILE"])
    if not log_file.is_file():
        return None, None, ({"error": "The application log file is missing."}, 404)

    try:
        records, invalid_lines = read_logs(log_file)
    except (OSError, UnicodeError) as error:
        app.logger.error("Could not read application log file: %s", error)
        return None, None, ({"error": "The application log file could not be read."}, 500)

    matching = filter_logs(
        records,
        level=filters["severity"],
        keyword=filters["keyword"],
        date=filters["date"],
    )
    return matching, invalid_lines, None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dashboard")
def dashboard_data():
    filters, error = _get_filters()
    if error:
        message, status = error
        return jsonify(error=message), status

    records, invalid_lines, error = _load_filtered_records(filters)
    if error:
        body, status = error
        return jsonify(body), status

    counts = Counter(record["level"] for record in records)
    errors = Counter(
        record["message"] for record in records if record["level"] == "ERROR"
    )
    serialized_records = [
        {
            "timestamp": record["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "severity": record["level"],
            "message": record["message"],
            "line_number": record["line_number"],
        }
        for record in records
    ]

    return jsonify(
        records=serialized_records,
        summary={
            "total_logs": len(records),
            "info": counts["INFO"],
            "warning": counts["WARNING"],
            "error": counts["ERROR"],
        },
        frequent_errors=[
            {"message": message, "count": count}
            for message, count in errors.most_common(5)
        ],
        invalid_lines=invalid_lines,
    )


@app.get("/api/export.csv")
def export_csv():
    filters, error = _get_filters()
    if error:
        message, status = error
        return jsonify(error=message), status

    records, _, error = _load_filtered_records(filters)
    if error:
        body, status = error
        return jsonify(body), status

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=["timestamp", "severity", "message", "line_number"],
    )
    writer.writeheader()
    for record in records:
        writer.writerow(
            {
                "timestamp": record["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "severity": record["level"],
                "message": record["message"],
                "line_number": record["line_number"],
            }
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="loglens-export.csv"'},
    )


if __name__ == "__main__":
    app.run()
