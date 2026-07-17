from __future__ import annotations
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

GENERATOR = Path(__file__).with_name("generate_gibraltar_brief.py")

class GibraltarBriefTests(unittest.TestCase):
    def test_generator_builds_safe_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = {
                "checked_at": "2026-07-17T00:00:00Z",
                "source": "USGS Earthquake Catalog",
                "status": "OK",
                "data_note_es": "Datos de prueba",
                "data_note_en": "Test data",
                "periods": {"24h": 1, "7d": 3, "30d": 8},
                "max_magnitude_30d": 3.2,
                "last_event": {"magnitude": 2.1, "place": "Alboran Sea", "time": "2026-07-16T22:00:00Z"},
                "events": []
            }
            (root / "seismicity.json").write_text(json.dumps(sample), encoding="utf-8")
            env = dict(os.environ, GIBRALTAR_ROOT=str(root))
            subprocess.run(["python", str(GENERATOR)], check=True, env=env, capture_output=True, text=True)
            brief = json.loads((root / "gibraltar-brief.json").read_text(encoding="utf-8"))
            social = json.loads((root / "gibraltar-social-drafts.json").read_text(encoding="utf-8"))
            self.assertIn(brief["health"], {"OK", "STALE"})
            self.assertEqual(brief["seismic"]["periods"]["30d"], 8)
            self.assertIn("no permiten inferir", brief["summary_es"])
            self.assertIn("utm_source=x", social["status_es"])
            self.assertTrue((root / "gibraltar-brief-feed.xml").exists())

if __name__ == "__main__":
    unittest.main()
