import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_secure_public_site as build
import generate_diario_estrecho as diary
import update_observatory as observatory
import validate_gibraltar as validator
from datetime import datetime, timezone


class PublicationTests(unittest.TestCase):
    def test_current_non_archived_diary_can_be_newer_than_archive(self):
        state = {
            "latest_entry": {"date": "2026-09-07"},
            "entries": [{"date": "2026-09-06"}, {"date": "2026-09-04"}],
        }
        self.assertTrue(validator.latest_date_is_consistent({"date": "2026-09-07"}, state))
        self.assertFalse(validator.latest_date_is_consistent({"date": "2026-09-04"}, state))

    def test_recent_check_does_not_make_old_ope_report_fresh(self):
        now = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
        with patch.object(observatory, "NOW", now):
            health = observatory.build_health({}, {}, {
                "checked_at": now.isoformat(), "report_date": "2026-08-15"
            }, {"date": "2026-09-01", "updated_at": now.isoformat()})
        self.assertEqual(health["components"][2]["state"], "stale")
        self.assertEqual(health["components"][2]["report_date"], "2026-08-15")
        self.assertEqual(health["components"][3]["state"], "fresh")

    def test_low_confidence_explains_which_sources_are_stale(self):
        detail, pending = observatory.confidence_context("BAJA", {
            "components": [
                {"name": "Radioavisos", "state": "fresh"},
                {"name": "Operación Paso del Estrecho", "state": "stale"},
            ]
        })
        self.assertEqual(pending, ["Operación Paso del Estrecho"])
        self.assertIn("Confianza baja", detail)
        self.assertIn("Operación Paso del Estrecho", detail)

    def test_change_since_yesterday_uses_previous_daily_snapshot(self):
        with patch.object(observatory, "LOCAL_TODAY", datetime(2026, 9, 24).date()):
            result = observatory.change_since_yesterday(
                {"label_es": "VIGILANCIA"},
                {"news_24h": 12},
                [{"date": "2026-09-23", "state_label": "NORMALIDAD OPERATIVA", "metrics": {"news_24h": 9}}],
            )
        self.assertEqual(result["reference_date"], "2026-09-23")
        self.assertIn("pasa de NORMALIDAD OPERATIVA a VIGILANCIA", result["summary_es"])
        self.assertIn("3 referencias más", result["summary_es"])

    def test_diary_metadata_tracks_current_editorial_engine(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(diary, "ARCHIVE_DIR", Path(folder)):
            entry = {"date": "2026-09-01", "headline": "La edición vigente", "summary": "Resumen", "source_count": 2, "editor_engine": "openrouter-free", "editor_assistant_status": "ok"}
            diary.sync_latest_metadata(entry)
            path = Path(folder) / "latest.json"
            content = path.read_text()
            metadata = json.loads(content)
            self.assertEqual(metadata["slug"], "2026-09-01.html")
            self.assertEqual(metadata["editor_engine"], "openrouter-free")
            self.assertEqual(metadata["editor_assistant_status"], "ok")
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

    def test_public_html_is_prerendered_from_one_timestamp_without_loading_copy(self):
        data = {
            "geopolitics.json": {
                "generated_at": "2026-09-24T08:00:00Z",
                "status": {
                    "maritime_status": {"es": "OPERATIVO"},
                    "maritime_note": {"es": "Corredor abierto."},
                    "border_pressure": {"es": "VIGILANCIA PREVENTIVA"},
                    "border_note": {"es": "Se mantiene durante 48 horas."},
                    "confidence": {"es": "MEDIA"},
                },
                "items": [],
            },
            "observatory.json": {
                "generated_at": "2026-09-24T10:06:33Z",
                "state": {
                    "label_es": "VIGILANCIA",
                    "confidence": "BAJA",
                    "confidence_explanation_es": "Confianza baja porque falta actualizar una fuente.",
                    "summary_es": "Seguimiento preventivo.",
                    "alert_level": {"label_es": "INFORMATIVO"},
                    "layers": {},
                },
                "metrics": {"news_24h": 18},
                "since_yesterday": {"summary_es": "Sin cambio material desde ayer."},
            },
            "health.json": {"overall": "stale"},
            "timeline.json": [],
        }
        home = '<p id="gwcStatusMeta">Cargando última comprobación…</p><p id="gwcConfidenceNote"></p><strong id="gwcStatusBorder">—</strong><p id="gwcNoteBorder"></p><div id="gwcNewsList">Cargando</div>'
        rendered_home = build.prerender_html(home, "index.html", data)
        self.assertNotIn("Cargando", rendered_home)
        self.assertIn("24/09/2026 · 12:06 (hora peninsular)", rendered_home)
        self.assertIn("VIGILANCIA PREVENTIVA", rendered_home)
        self.assertIn("Confianza baja porque", rendered_home)

        situation = '<b data-gwo-state>Cargando…</b><small data-gwo-updated>—</small><strong data-gwo-confidence>—</strong><p data-gwo-confidence-note>—</p><p data-gwo-summary>—</p><strong data-gwo-metric="news_24h">—</strong><p data-gwo-since-yesterday>—</p>'
        rendered_situation = build.prerender_html(situation, "situacion-actual.html", data)
        self.assertNotIn("Cargando", rendered_situation)
        self.assertIn("VIGILANCIA", rendered_situation)
        self.assertIn("18", rendered_situation)
        self.assertIn("Sin cambio material desde ayer.", rendered_situation)

    def test_updates_trigger_public_deployment(self):
        root = Path(__file__).resolve().parent
        deploy = (root / ".github/workflows/deploy-gibraltar-secure.yml").read_text()
        update = (root / ".github/workflows/update-gibraltar.yml").read_text()
        self.assertIn("workflow_run:", deploy)
        self.assertIn('workflows: ["Actualizar Gibraltar Watch"]', deploy)
        self.assertIn("conclusion == 'success'", deploy)
        self.assertIn("python generate_newsletter.py", update)
        self.assertIn("python validate_gibraltar.py", update)

    def test_public_source_pages_do_not_link_to_private_json(self):
        root = Path(__file__).resolve().parent
        strategy = (root / "install_gibraltar_strategy.py").read_text(encoding="utf-8")
        llms = (root / "llms.txt").read_text(encoding="utf-8")
        self.assertNotIn("geopolitics-sources.json", strategy)
        self.assertNotIn("estrechogibraltar.com/geopolitics.json", llms)

    def test_no_paid_editorial_client_or_credentials(self):
        root = Path(__file__).resolve().parent
        engine = (root / "generate_diario_estrecho.py").read_text() + (root / "generate_diario.py").read_text()
        workflow = (root / ".github/workflows/update-gibraltar.yml").read_text()
        for forbidden in ("OPENAI_API_KEY", "DIARIO_AI", "from openai", "responses.parse"):
            self.assertNotIn(forbidden, engine + workflow)
        self.assertNotIn("pypdf openai", workflow)


if __name__ == "__main__":
    unittest.main()
