import unittest
from datetime import datetime, timezone

from update_ope import apply_lifecycle, parse_date, rows, totals


class OpeParserTests(unittest.TestCase):
    def test_date(self):
        self.assertEqual(parse_date("1 de agosto de 2026").isoformat(), "2026-08-01")

    def test_rows(self):
        result = rows("Algeciras/Tánger-Med 35 25482 7312")
        self.assertEqual(result[0]["passengers"], 25482)

    def test_totals(self):
        data = totals("Total general día 86 49908 13404", r"Total general d[ií]a")
        self.assertEqual(data["vehicles"], 13404)

    def test_season_complete_is_historical_not_stale(self):
        data = {"season_start": "2026-06-15", "season_end": "2026-09-15", "report_date": "2026-08-15"}
        result = apply_lifecycle(data, datetime(2026, 9, 28, tzinfo=timezone.utc))
        self.assertEqual(result["lifecycle"], "SEASON_COMPLETE")
        self.assertTrue(result["historical"])

    def test_active_season_with_old_report_is_stale(self):
        data = {"season_start": "2026-06-15", "season_end": "2026-09-15", "report_date": "2026-07-01"}
        result = apply_lifecycle(data, datetime(2026, 8, 1, tzinfo=timezone.utc))
        self.assertEqual(result["lifecycle"], "STALE")


if __name__ == "__main__":
    unittest.main()
