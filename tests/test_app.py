import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


class TestDashboardApp(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp.name) / "application.log"
        self.log_path.write_text(
            "2026-10-23 09:00:00 INFO Started\n"
            "2026-10-23 09:01:00 ERROR Database failed\n"
            "2026-10-24 10:00:00 ERROR Database failed\n"
            "2026-10-24 10:01:00 WARNING Slow response\n"
            "Invalid log line\n",
            encoding="utf-8",
        )
        app.config.update(TESTING=True, LOG_FILE=self.log_path)
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_dashboard_returns_real_records_and_summary(self):
        response = self.client.get("/api/dashboard")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["summary"], {
            "total_logs": 4,
            "info": 1,
            "warning": 1,
            "error": 2,
        })
        self.assertEqual(data["frequent_errors"], [
            {"message": "Database failed", "count": 2}
        ])
        self.assertEqual(data["invalid_lines"], 1)

    def test_dashboard_applies_severity_keyword_and_date_filters(self):
        response = self.client.get(
            "/api/dashboard?severity=ERROR&keyword=database&date=2026-10-24"
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["summary"]["total_logs"], 1)
        self.assertEqual(data["records"][0]["message"], "Database failed")

    def test_empty_filter_result_returns_zero_summary(self):
        response = self.client.get("/api/dashboard?keyword=not-found")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["summary"]["total_logs"], 0)
        self.assertEqual(data["records"], [])
        self.assertEqual(data["frequent_errors"], [])

    def test_dashboard_rejects_invalid_filters(self):
        for query in ("?severity=DEBUG", "?date=2026-02-30", "?date=10-23-2026"):
            with self.subTest(query=query):
                response = self.client.get("/api/dashboard" + query)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

    def test_dashboard_page_and_assets_are_available(self):
        page = self.client.get("/")

        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Application <span>overview</span>", page.data)
        css = self.client.get("/static/css/dashboard.css")
        self.assertEqual(css.status_code, 200)
        css.close()

        javascript = self.client.get("/static/js/dashboard.js")
        self.assertEqual(javascript.status_code, 200)
        javascript.close()

    def test_export_returns_filtered_csv(self):
        response = self.client.get("/api/export.csv?severity=ERROR")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn("Database failed", response.get_data(as_text=True))
        self.assertIn('filename="loglens-export.csv"', response.headers["Content-Disposition"])

    def test_missing_log_file_returns_json_error(self):
        app.config["LOG_FILE"] = Path(self.temp.name) / "missing.log"

        response = self.client.get("/api/dashboard")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
