import unittest
import generate_diario_estrecho as diary
from diary_evidence import archive_decision, source_key
from ope_analysis import audit
from publication_quality import apply_policy


class EditorialQualityTests(unittest.TestCase):
    def item(self, source, path):
        return {"title": f"Noticia de {source} sobre el puerto", "source": source, "url": f"https://news.google.com/rss/articles/{path}",
                "published_at": diary.NOW_UTC.isoformat(), "category": "ports", "weight": 3}

    def test_google_news_is_not_the_source(self):
        a, b = self.item("Medio A", "a"), self.item("Medio B", "b")
        self.assertNotEqual(source_key(a), source_key(b))
        self.assertEqual(len(diary.select_items([a, b, self.item("Medio C", "c")])), 3)

    def test_volume_does_not_create_archive(self):
        status = {"maritime_status": {"es": "OPERATIVO"}}
        items = [self.item("A", "a"), self.item("B", "b")]
        _, snapshot, keys = archive_decision(status, [], {})
        result = archive_decision(status, items, {"status_snapshot": snapshot, "source_keys": keys})
        self.assertFalse(result[0])
        self.assertTrue(archive_decision({"maritime_status": {"es": "INCIDENCIA"}}, items, {"status_snapshot": snapshot, "source_keys": keys})[0])

    def test_unreviewed_full_digest_is_not_indexable(self):
        self.assertFalse(diary.seo_indexable("full", {"maritime_status": {"es": "INCIDENCIA"}}, [self.item("A", "a")]))

    def test_opinion_does_not_invent_border_measurement(self):
        text = diary.fallback_section_text("Ceuta y Melilla", {}, [self.item("A", "a")])
        self.assertIn("no mide la presión actual", text)
        self.assertNotIn("se sitúa en ALTA", text)

    def test_incomplete_route_data_is_not_zero(self):
        data = {"departure": {"day": {"passengers": 100}, "routes": [{"passengers": 70}]}}
        rows = audit(data)
        self.assertIn(("departure", "passengers", 100, 70, 30), rows)
        self.assertIn(("return", "passengers", None, None, None), rows)

    def test_ads_removed_from_legacy_and_current_diaries(self):
        page = '<html><head><meta name="robots" content="index,follow"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script></head><body><main>Contenido</main></body></html>'
        for path in ("diario/2026-08-31.html", "diario/actual.html", "newsletter/latest.html"):
            result = apply_policy(page, path)
            self.assertIn("noindex,follow", result)
            self.assertNotIn("adsbygoogle", result)
            self.assertIn("Contenido", result)

    def test_original_analysis_is_not_excluded(self):
        result = apply_policy("<html><head></head><body><main>Análisis</main></body></html>", "auditoria-datos-ope.html")
        self.assertNotIn("noindex", result)
