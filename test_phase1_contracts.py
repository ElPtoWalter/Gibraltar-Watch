import json
import unittest
from pathlib import Path

import build_secure_public_site as public_build


ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class PhaseOneContractTests(unittest.TestCase):
    def test_event_store_has_stable_auditable_shape(self):
        payload = load("events.json")
        self.assertGreater(payload.get("event_count", 0), 0)
        events = payload["events"]
        ids = [event["event_id"] for event in events]
        self.assertEqual(len(ids), len(set(ids)))
        for event in events:
            self.assertTrue(event["event_id"].startswith("evt_"))
            self.assertIn(event["verification_status"], {
                "CONFIRMED_PRIMARY", "CONFIRMED_MULTI_SOURCE", "SINGLE_SOURCE",
                "DECLARATION_ONLY", "CONFLICTING", "UNCONFIRMED",
            })
            self.assertIsInstance(event["sources"], list)
            self.assertIsInstance(event["articles"], list)
            self.assertGreaterEqual(event["importance"], 0)
            self.assertLessEqual(event["importance"], 100)

    def test_diary_trace_links_packet_events_and_sources(self):
        latest = load("diario/latest.json")
        self.assertEqual(latest["validator_version"], 2)
        self.assertRegex(latest["factual_packet_hash"], r"^[0-9a-f]{64}$")
        self.assertIsInstance(latest["event_ids"], list)
        self.assertIsInstance(latest["source_ids"], list)
        self.assertIsInstance(latest["fallback_used"], bool)
        self.assertIn("verification_summary", latest)

    def test_health_separates_sources_pipeline_publication_and_assessment(self):
        health = load("health.json")
        self.assertEqual(health["schema_version"], 2)
        self.assertIn(health["overall"], {"HEALTHY", "DEGRADED", "STALE", "ERROR"})
        self.assertIsInstance(health["source_health"], list)
        self.assertIn(health["pipeline_health"]["state"], {"HEALTHY", "DEGRADED", "STALE", "ERROR"})
        self.assertIn("publication_health", health)
        self.assertTrue(health["operational_assessment"]["separate_from_source_health"])

    def test_completed_ope_is_historical_and_not_an_active_failure(self):
        ope = load("ope-2026.json")
        self.assertEqual(ope["lifecycle"], "SEASON_COMPLETE")
        self.assertTrue(ope["historical"])
        component = next(item for item in load("health.json")["components"] if item["name"] == "Operación Paso del Estrecho")
        self.assertEqual(component["state"], "historical")
        self.assertEqual(component["lifecycle"], "SEASON_COMPLETE")

    def test_ope_public_html_is_server_rendered_for_crawlers(self):
        source = (ROOT / "operacion-paso-estrecho-2026.html").read_text(encoding="utf-8")
        rendered = public_build.prerender_ope(source, load("ope-2026.json"), "es")
        self.assertIn("Temporada finalizada", rendered)
        self.assertIn("15 de agosto de 2026", rendered)
        self.assertNotIn('data-ope="departure_passengers_day">—<', rendered)
        self.assertIn("20260815_InformeOPE.pdf", rendered)


if __name__ == "__main__":
    unittest.main()
