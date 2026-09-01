import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_secure_public_site as build
import generate_diario_estrecho as diary
import update_observatory as observatory
from datetime import datetime, timezone


class PublicationTests(unittest.TestCase):
    def test_recent_check_does_not_make_old_ope_report_fresh(self):
        now = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
        with patch.object(observatory, "NOW", now):
            health = observatory.build_health({}, {}, {
                "checked_at": now.isoformat(), "report_date": "2026-08-15"
            }, {"date": "2026-09-01", "updated_at": now.isoformat()})
        self.assertEqual(health["components"][2]["state"], "stale")
        self.assertEqual(health["components"][2]["report_date"], "2026-08-15")
        self.assertEqual(health["components"][3]["state"], "fresh")

    def test_diary_metadata_tracks_current_editorial_engine(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(diary, "ARCHIVE_DIR", Path(folder)):
            entry = {"date": "2026-09-01", "headline": "La edición vigente", "summary": "Resumen", "source_count": 2}
            diary.sync_latest_metadata(entry)
            path = Path(folder) / "latest.json"
            content = path.read_text()
            self.assertEqual(json.loads(content)["slug"], "2026-09-01.html")
            diary.sync_latest_metadata(entry)
            self.assertEqual(content, path.read_text())

    def test_public_build_keeps_manifest_and_newsletter_download(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "newsletter").mkdir()
            (root / "newsletter/latest.txt").write_text("Public newsletter")
            (root / "site.webmanifest").write_text('{"name":"Gibraltar"}')
            (root / "internal.json").write_text('{"private":true}')
            (root / "_site").mkdir()
            with patch.object(build, "ROOT", root), patch.object(build, "OUT", root / "_site"):
                build.copy_public("/runtime.js")
                self.assertTrue((root / "_site/site.webmanifest").exists())
                self.assertTrue((root / "_site/newsletter/latest.txt").exists())
                self.assertFalse((root / "_site/internal.json").exists())

    def test_updates_trigger_public_deployment(self):
        root = Path(__file__).resolve().parent
        deploy = (root / ".github/workflows/deploy-gibraltar-secure.yml").read_text()
        update = (root / ".github/workflows/update-gibraltar.yml").read_text()
        self.assertIn("workflow_run:", deploy)
        self.assertIn('workflows: ["Actualizar Gibraltar Watch"]', deploy)
        self.assertIn("conclusion == 'success'", deploy)
        self.assertIn("python generate_newsletter.py", update)
        self.assertIn("python validate_gibraltar.py", update)

    def test_no_paid_editorial_client_or_credentials(self):
        root = Path(__file__).resolve().parent
        engine = (root / "generate_diario_estrecho.py").read_text()
        workflow = (root / ".github/workflows/update-gibraltar.yml").read_text()
        for forbidden in ("OPENAI_API_KEY", "DIARIO_AI", "from openai", "responses.parse"):
            self.assertNotIn(forbidden, engine + workflow)
        self.assertNotIn("pypdf openai", workflow)


if __name__ == "__main__":
    unittest.main()
