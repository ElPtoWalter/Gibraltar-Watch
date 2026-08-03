from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess
import os


class InstallerTests(unittest.TestCase):
    def test_installer_is_idempotent_on_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            html = '<!doctype html><html lang="es"><head><title>Old</title><meta name="description" content="old"></head><body><header><nav class="site-nav"><a href="x">x</a></nav></header><main><section class="hero home-hero"><h1>old</h1></section><section class="truth-banner">truth</section><section class="dashboard" id="panel">dash</section><section class="faq-section">faq</section></main><footer class="site-footer">old</footer></body></html>'
            (root/'index.html').write_text(html,encoding='utf-8')
            (root/'sitemap.xml').write_text('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>',encoding='utf-8')
            for name in ['gibraltar-strategy.css','gibraltar-strategy.js','install_gibraltar_strategy.py']:
                shutil.copy(Path(__file__).parent/name,root/name)
            subprocess.run(['python','install_gibraltar_strategy.py'],cwd=root,check=True)
            once=(root/'index.html').read_text(encoding='utf-8')
            subprocess.run(['python','install_gibraltar_strategy.py'],cwd=root,check=True)
            twice=(root/'index.html').read_text(encoding='utf-8')
            self.assertEqual(once,twice)
            self.assertEqual(twice.count('GW_STRATEGY_HOME_START'),1)
            self.assertEqual(twice.count('gibraltar-strategy.css'),1)
            self.assertIn('tráfico, economía y geopolítica',twice)


if __name__=='__main__':
    unittest.main()
