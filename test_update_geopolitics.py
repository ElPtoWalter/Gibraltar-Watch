from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

import update_geopolitics as u


class GeopoliticsTests(unittest.TestCase):
    def test_parse_rss(self):
        rss = b'''<?xml version="1.0"?><rss><channel><item><title>Ceuta border crisis - Reuters</title><link>https://example.com/a</link><pubDate>Sun, 03 Aug 2026 10:00:00 GMT</pubDate><source>Reuters</source></item></channel></rss>'''
        items = u.parse_rss(rss, "ceuta", "en")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "Reuters")
        self.assertEqual(items[0].weight, 5)

    def test_high_border_pressure_requires_signals(self):
        now = datetime.now(timezone.utc).isoformat()
        items = [
            u.NewsItem("Thousands cross into Ceuta in massive border rush", "Reuters", "x", now, "ceuta", "en", 5),
            u.NewsItem("Ceuta emergency after migrant crisis", "BBC", "y", now, "ceuta", "en", 4),
        ]
        status = u.classify(items)
        self.assertEqual(status["border_pressure"]["en"], "HIGH")
        self.assertNotEqual(status["maritime_status"]["en"], "POSSIBLE DISRUPTION")

    def test_single_closure_headline_does_not_close_strait(self):
        now = datetime.now(timezone.utc).isoformat()
        items = [u.NewsItem("Rumour says Strait closed", "Unknown", "x", now, "traffic", "en", 1)]
        status = u.classify(items)
        self.assertEqual(status["maritime_status"]["en"], "OPERATIONAL")

    def test_two_trusted_maritime_sources_raise_possible_disruption(self):
        now = datetime.now(timezone.utc).isoformat()
        items = [
            u.NewsItem("Shipping halt reported in Strait", "Reuters", "x", now, "traffic", "en", 5),
            u.NewsItem("Navigation suspended in Strait", "BBC", "y", now, "traffic", "en", 4),
        ]
        status = u.classify(items)
        self.assertEqual(status["maritime_status"]["en"], "POSSIBLE DISRUPTION")

    def test_preventive_border_measures_do_not_drop_directly_to_low(self):
        now = datetime.now(timezone.utc).isoformat()
        items = [
            u.NewsItem("Gobierno refuerza la frontera de Ceuta", "RTVE", "x", now, "ceuta", "es", 4),
            u.NewsItem("Despliegue preventivo ante nuevos llamamientos", "El País", "y", now, "melilla", "es", 3),
        ]
        status = u.classify(items)
        self.assertEqual(status["border_pressure"]["es"], "VIGILANCIA PREVENTIVA")
        self.assertEqual(status["border_watch"]["signal_sources"], 2)

    def test_preventive_watch_is_held_for_48_hours_and_then_expires(self):
        fixed_now = datetime(2026, 9, 24, 12, tzinfo=timezone.utc)
        previous = {
            "generated_at": (fixed_now - timedelta(hours=24)).isoformat(),
            "status": {
                "border_pressure": {"es": "VIGILANCIA PREVENTIVA"},
                "border_watch": {"last_signal_at": (fixed_now - timedelta(hours=24)).isoformat()},
            },
        }
        with patch.object(u, "NOW", fixed_now):
            held = u.classify([], previous)
        self.assertEqual(held["border_pressure"]["es"], "VIGILANCIA PREVENTIVA")

        previous["status"]["border_watch"]["last_signal_at"] = (fixed_now - timedelta(hours=49)).isoformat()
        with patch.object(u, "NOW", fixed_now):
            expired = u.classify([], previous)
        self.assertEqual(expired["border_pressure"]["es"], "BAJA / SIN SEÑALES RECIENTES")


if __name__ == "__main__":
    unittest.main()
