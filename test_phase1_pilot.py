import os
import unittest
from pathlib import Path
from unittest.mock import patch

import pilot_gemini_phase1 as pilot


ROOT = Path(__file__).resolve().parent
COMPLETE_DRAFT = {
    "headline": "Titular factual",
    "deck": "Resumen factual",
    "situation": ["Situación"],
    "sections": [{"title": "Sección", "paragraph": "Texto"}],
    "meaning": ["Significado"],
    "watch": ["Vigilancia"],
}


class PhaseOnePilotTests(unittest.TestCase):
    def test_real_data_contains_enough_references_for_isolated_pilot(self):
        data = pilot.journal.load_json(ROOT / "geopolitics.json", {})
        selected = pilot.journal.select_items(data.get("items", []), hours=96)
        self.assertGreaterEqual(len(selected), 2)
        self.assertGreaterEqual(len({pilot.journal.source_key(item) for item in selected}), 2)

    def test_local_and_gemini_compare_the_same_packet_without_publishing(self):
        digest = "a" * 64

        def fake_build(_status, _selected, _mode, _events, _previous, trace):
            is_gemini = bool(os.environ.get("GEMINI_API_KEY"))
            trace.update({
                "factual_packet_hash": digest,
                "validator_version": 2,
                "event_ids": ["evt_real"],
                "source_ids": ["rtve", "efe"],
                "verification_summary": {"TOTAL": 1},
                "attempts": [{"provider": "gemini", "status": "ok"}] if is_gemini else [],
            })
            return COMPLETE_DRAFT, ("gemini" if is_gemini else "rules"), ("ok" if is_gemini else "local-only")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-only-value"}, clear=False), patch.object(pilot.journal, "build_draft", side_effect=fake_build):
            report = pilot.run_pilot(ROOT)
        self.assertTrue(report["passed"])
        self.assertFalse(report["published"])
        self.assertTrue(report["checks"]["same_factual_packet"])
        self.assertEqual(report["local"]["engine"], "rules")
        self.assertEqual(report["gemini"]["engine"], "gemini")


if __name__ == "__main__":
    unittest.main()
