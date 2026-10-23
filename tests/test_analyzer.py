
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyzer import read_logs, filter_logs


class TestLogLens(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.log"

        self.path.write_text(
            "2026-10-23 09:00:00 INFO Started\n"
            "2026-10-23 09:01:00 ERROR Database failed\n"
            "2026-10-23 09:02:00 ERROR API failed\n"
            "2026-10-24 10:00:00 WARNING Slow response\n"
            "Invalid log line\n",
            encoding="utf-8"
        )

        self.records, self.invalid = read_logs(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_read_logs(self):
        self.assertEqual(len(self.records), 4)
        self.assertEqual(self.invalid, 1)

    def test_filter_errors(self):
        result = filter_logs(self.records, level="ERROR")
        self.assertEqual(len(result), 2)

    def test_filter_keyword(self):
        result = filter_logs(self.records, keyword="database")
        self.assertEqual(len(result), 1)

    def test_filter_date(self):
        result = filter_logs(self.records, date="2026-10-24")
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
