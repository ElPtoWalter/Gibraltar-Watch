from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import emit_observatory_alert as alerts
import install_gibraltar_observatory as installer
import postprocess_diario as diary
import update_observatory as obs


class ObservatoryLogicTests(unittest.TestCase):
    def test_maritime_closure_is_operational_alert(self):
        status = {
            "maritime_status": {"es": "CERRADO"},
            "border_pressure": {"es": "BAJA"},
            "bilateral_tension": {"es": "ESTABLE"},
            "security_status": {"es": "SIN ALERTA ESPECÍFICA"},
        }
        state = obs.overall_state(status, "healthy")
        self.assertEqual(state["code"], "operational_alert")
        self.assertEqual(state["severity"], 4)
        self.assertIn("verificarse", state["summary_es"])

    def test_political_watch_does_not_become_closure(self):
        status = {
            "maritime_status": {"es": "OPERATIVO"},
            "border_pressure": {"es": "ALTA"},
            "bilateral_tension": {"es": "VIGILANCIA"},
            "security_status": {"es": "SIN ALERTA ESPECÍFICA"},
        }
        state = obs.overall_state(status, "healthy")
        self.assertNotEqual(state["code"], "operational_alert")
        self.assertIn("sin que ello implique", state["summary_es"])

    def test_security_no_alert_is_zero(self):
        self.assertEqual(obs.severity_for("security", "SIN ALERTA ESPECÍFICA"), 0)

    def test_alert_levels(self):
        self.assertEqual(obs.alert_level_for({"severity": 0})["code"], "informational")
        self.assertEqual(obs.alert_level_for({"severity": 2})["code"], "relevant")
        self.assertEqual(obs.alert_level_for({"severity": 3})["code"], "important")
        self.assertEqual(obs.alert_level_for({"severity": 4})["code"], "urgent")

    def test_anomalies_need_history(self):
        current = {"news_24h": 50, "seismic_7d": 50, "ope_passengers_day": 100000}
        self.assertEqual(obs.detect_anomalies(current, [{}] * 6), [])

    def test_anomaly_after_enough_history(self):
        history = [{"metrics": {"news_24h": 3, "seismic_7d": 1, "ope_passengers_day": 1000}} for _ in range(8)]
        out = obs.detect_anomalies({"news_24h": 10, "seismic_7d": 6, "ope_passengers_day": 2000}, history)
        keys = {x["key"] for x in out}
        self.assertIn("news-volume", keys)
        self.assertIn("seismic-volume", keys)
        self.assertIn("ope-mobility", keys)

    def test_metrics_match_current_project_schema(self):
        seismic = {"periods": {"24h": 1, "7d": 2, "30d": 4}, "max_magnitude_30d": 3.2}
        geo = {"items": [{"published_at": obs.iso(), "source": "A"}]}
        ope = {"report_date": "2026-08-08", "departure": {"day": {"passengers": 10, "vehicles": 2, "rotations": 1}}, "return": {"day": {"passengers": 20, "vehicles": 3, "rotations": 2}}}
        latest = {"date": "2026-08-10", "source_count": 7, "generator": "determinista"}
        m = obs.metrics(seismic, geo, ope, latest)
        self.assertEqual(m["seismic_7d"], 2)
        self.assertEqual(m["ope_passengers_day"], 30)
        self.assertEqual(m["ope_vehicles_day"], 5)
        self.assertEqual(m["ope_rotations_day"], 3)
        self.assertEqual(m["diary_source_count"], 7)


class InstallerTests(unittest.TestCase):
    def test_home_patch_is_idempotent(self):
        html = '<html><head></head><body><main><section class="gwc-hero"><h1>X</h1></section><!-- GW_DIARY_HOME_START --></main><footer><div class="gwc-footer-bottom"></div></footer></body></html>'
        once = installer.patch_home(html)
        twice = installer.patch_home(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count(installer.START_LIVE), 1)
        self.assertEqual(once.count(installer.START_TIMELINE), 1)
        self.assertEqual(once.count('gw-observatory.css'), 1)

    def test_home_fallback_works_without_known_hero(self):
        html = '<html><head></head><body><main><h1>X</h1></main><footer></footer></body></html>'
        out = installer.patch_home(html)
        self.assertIn(installer.START_LIVE, out)
        self.assertLess(out.index(installer.START_LIVE), out.index('<h1>X</h1>'))

    def test_diary_patch_does_not_rewrite_article_text(self):
        html = '<html><head></head><body><main><div class="diary-byline">Autor</div><p id="fact">Texto factual original.</p></main><footer></footer></body></html>'
        once = diary.patch(html)
        twice = diary.patch(once)
        self.assertEqual(once, twice)
        self.assertIn('Texto factual original.', once)
        self.assertEqual(once.count(diary.START), 1)


class AlertOutputTests(unittest.TestCase):
    def test_emit_outputs_material_transition(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = {
                "state": {"code": "high_watch", "label_es": "VIGILANCIA ALTA", "severity": 3, "confidence": "MEDIA", "summary_es": "X", "alert_level": {"code": "important", "label_es": "IMPORTANTE"}},
                "changes": {"state_changed": True},
            }
            (root / "observatory.json").write_text(json.dumps(payload), encoding="utf-8")
            output = root / "out.txt"
            with mock.patch.object(alerts, "ROOT", root), mock.patch.object(alerts, "OBS", root / "observatory.json"), mock.patch.dict(os.environ, {"GITHUB_OUTPUT": str(output)}):
                self.assertEqual(alerts.main(), 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("notify=true", text)
            self.assertIn("alert_label=IMPORTANTE", text)


if __name__ == "__main__":
    unittest.main()
