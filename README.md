# LogLens — Application Log Analyzer

LogLens is a Python-based application log analyzer with a Flask-powered monitoring dashboard. It analyzes the real `logs/application.log` file and presents its entries, severity totals, and recurring errors in a responsive web interface.

## Features

- Parse application logs containing timestamps, severity levels, and messages.
- Count INFO, WARNING, and ERROR events from the current log file.
- Identify frequently occurring errors.
- Filter logs by severity, keyword, and date.
- Export matching records to CSV.
- Detect and skip invalid log lines.
- Handle missing or unreadable log files and invalid filter values.
- Includes automated unit tests using Python's `unittest` framework.

## Project structure

```text
loglens/
├── analyzer.py
├── app.py
├── logs/
│   └── application.log
├── reports/
│   └── log_summary.csv
├── static/
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
├── templates/
│   └── index.html
├── tests/
│   ├── test_analyzer.py
│   └── test_app.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or later
- Flask

## Run the dashboard

Open PowerShell in the project directory and install Flask:

```powershell
py -m pip install -r requirements.txt
```

Start the development server:

```powershell
py app.py
```

Open **http://127.0.0.1:5000** in your browser. The dashboard reads `logs/application.log` when data is requested; it does not use placeholder records or hardcoded statistics.

The JSON endpoint supports optional `severity`, `keyword`, and `date` query parameters:

```powershell
Invoke-RestMethod "http://127.0.0.1:5000/api/dashboard?severity=ERROR&keyword=database&date=2026-10-23"
```

CSV export uses the same filters at `/api/export.csv`.

## Run the command-line analyzer

The original CLI is unchanged and remains available:

```powershell
py analyzer.py
py analyzer.py --level ERROR --keyword database --date 2026-10-23
py analyzer.py --level ERROR --export
```

The default CLI report is saved to `reports/log_summary.csv`.

## Run automated tests

```powershell
py -m unittest discover -s tests -v
```

**Author:** Preetam Patil
