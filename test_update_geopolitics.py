from datetime import datetime, timezone
import unittest

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


if __name__ == "__main__":
    unittest.main()
