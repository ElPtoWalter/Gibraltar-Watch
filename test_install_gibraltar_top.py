from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

INSTALLER = Path(__file__).with_name("install_gibraltar_top.py")
CSS = Path(__file__).with_name("gibraltar-top.css")
JS = Path(__file__).with_name("gibraltar-top.js")


class InstallerTests(unittest.TestCase):
    def test_installer_is_idempotent_and_patches_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copy2(INSTALLER, root / "install_gibraltar_top.py")
            shutil.copy2(CSS, root / "gibraltar-top.css")
            shutil.copy2(JS, root / "gibraltar-top.js")
            home = '''<!DOCTYPE html><html lang="es"><head><link href="styles.css" rel="stylesheet"></head><body><div class="site-shell"><header class="site-header"><nav class="site-nav"><a href="index.html">Inicio</a><a href="sismicidad.html">Sismicidad</a><a href="metodologia.html">Metodología</a></nav></header><main><section class="dashboard" id="panel"><article>Estado</article></section><section class="faq-section"><h2>Preguntas</h2></section></main><footer class="site-footer"><nav><a href="fuentes.html">Fuentes</a></nav></footer></div></body></html>'''
            en = home.replace('lang="es"','lang="en"').replace('index.html">Inicio','en.html">Home').replace('sismicidad.html">Sismicidad','en-seismicity.html">Seismicity').replace('metodologia.html">Metodología','en-methodology.html">Methodology').replace('fuentes.html">Fuentes','en-sources.html">Sources')
            (root / "index.html").write_text(home, encoding="utf-8")
            (root / "en.html").write_text(en, encoding="utf-8")
            (root / "sismicidad.html").write_text(home, encoding="utf-8")
            (root / "sitemap.xml").write_text('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', encoding="utf-8")
            (root / "robots.txt").write_text('User-agent: *\nAllow: /\n', encoding="utf-8")

            for _ in range(2):
                subprocess.run(["python", "install_gibraltar_top.py"], cwd=root, check=True, capture_output=True, text=True)

            es_text = (root / "index.html").read_text(encoding="utf-8")
            en_text = (root / "en.html").read_text(encoding="utf-8")
            sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
            self.assertEqual(es_text.count("GT_HOME_BRIEF_START"), 1)
            self.assertEqual(es_text.count("GT_HOME_ANALYSIS_START"), 1)
            self.assertEqual(es_text.count("GT_TRUST_START"), 1)
            self.assertEqual(es_text.count("gibraltar-top.css"), 1)
            self.assertEqual(es_text.count("gibraltar-top.js"), 1)
            self.assertIn('href="parte-diario.html"', es_text)
            self.assertIn('href="analisis.html"', es_text)
            self.assertIn('href="en-daily-brief.html"', en_text)
            self.assertIn('href="en-analysis.html"', en_text)
            self.assertEqual(sitemap.count("parte-diario.html"), 1)
            self.assertTrue((root / ".nojekyll").exists())
            self.assertIn("GT_EDITORIAL_RECORD", (root / "sismicidad.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
