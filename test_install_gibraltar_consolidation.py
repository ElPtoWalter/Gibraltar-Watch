import importlib.util
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

MODULE_PATH = Path(__file__).with_name('install_gibraltar_consolidation.py')
spec = importlib.util.spec_from_file_location('consolidation', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)

SAMPLE_ES = '''<!doctype html><html lang="es"><head><title>Old</title><meta name="description" content="old"></head><body><header><nav class="site-nav"><a href="index.html">Old</a></nav></header><main><section><h1>Old home</h1></section></main><footer class="site-footer">Old footer</footer></body></html>'''
SAMPLE_EN = SAMPLE_ES.replace('lang="es"', 'lang="en"').replace('Old home', 'Old English home')

class ConsolidationTests(unittest.TestCase):
    def test_idempotent_home_and_valid_sitemap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'index.html').write_text(SAMPLE_ES, encoding='utf-8')
            (root / 'en.html').write_text(SAMPLE_EN, encoding='utf-8')
            (root / 'trafico.html').write_text(SAMPLE_ES, encoding='utf-8')
            mod.ROOT = root
            mod.main()
            first = (root / 'index.html').read_text(encoding='utf-8')
            mod.main()
            second = (root / 'index.html').read_text(encoding='utf-8')
            self.assertEqual(first, second)
            self.assertEqual(second.count('GWC_HOME_START'), 1)
            self.assertEqual(second.count('gibraltar-consolidated.css'), 1)
            self.assertEqual(second.count('gibraltar-consolidated.js'), 1)
            self.assertIn('tráfico, economía y poder', second)
            self.assertIn('gwc-nav-group', second)
            tree = ET.parse(root / 'sitemap.xml')
            locs = [el.text for el in tree.getroot().iter() if el.tag.endswith('loc')]
            self.assertIn('https://estrechogibraltar.com/', locs)
            self.assertIn('https://estrechogibraltar.com/trafico.html', locs)

    def test_home_has_unique_ids(self):
        ids = re.findall(r'\bid="([^"]+)"', mod.HOME_ES)
        self.assertEqual(len(ids), len(set(ids)))
        ids_en = re.findall(r'\bid="([^"]+)"', mod.HOME_EN)
        self.assertEqual(len(ids_en), len(set(ids_en)))

if __name__ == '__main__':
    unittest.main()
