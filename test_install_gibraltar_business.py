import tempfile
import unittest
from pathlib import Path

import install_gibraltar_business as installer


class TestBusinessInstaller(unittest.TestCase):
    def test_adsense_identity_is_ready_without_enabling_empty_slots(self):
        root = Path(__file__).resolve().parent
        config = (root / "gw-monetization-config.js").read_text(encoding="utf-8")
        business = (root / "gw-business.js").read_text(encoding="utf-8")
        ads_txt = (root / "ads.txt").read_text(encoding="utf-8")
        archive = (root / "generate_diario_estrecho.py").read_text(encoding="utf-8")

        self.assertIn('client: "ca-pub-1713078636060241"', config)
        self.assertIn("enabled: false", config)
        self.assertIn("pub-1713078636060241", ads_txt)
        self.assertIn('script[src*="pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]', business)
        self.assertNotIn('pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=', archive)

    def test_legal_copy_matches_the_prepared_but_inactive_state(self):
        root = Path(__file__).resolve().parent
        privacy = (root / "privacidad.html").read_text(encoding="utf-8")
        cookies = (root / "cookies.html").read_text(encoding="utf-8")
        self.assertIn("El código base de AdSense puede cargarse para verificar el sitio", privacy)
        self.assertIn("El identificador de editor está configurado", cookies)
        self.assertNotIn("hasta introducir un identificador real", cookies)

    def test_assets_are_exactly_idempotent_and_old_fix_is_removed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'sample.html'
            p.write_text(
                '<html><head><script defer src="gibraltar-ui-fixes.js"></script></head>'
                '<body><footer></footer></body></html>',
                encoding='utf-8',
            )
            first = installer.patch_base(p)
            p.write_text(first, encoding='utf-8')
            second = installer.patch_base(p)
            self.assertEqual(first, second)
            self.assertEqual(second.count('gw-business.css'), 1)
            self.assertEqual(second.count('gw-business.js'), 1)
            self.assertEqual(second.count('gw-monetization-config.js'), 1)
            self.assertEqual(second.count('gw:last-reviewed'), 1)
            self.assertNotIn('gibraltar-ui-fixes.js', second)

    def test_home_blocks_are_exactly_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'index.html'
            p.write_text(
                '<html><head></head><body><main>'
                '<section class="gwc-traffic-economy"></section>'
                '<section class="gwc-contact-cta"></section>'
                '</main><footer></footer></body></html>',
                encoding='utf-8',
            )
            first = installer.patch_content(p, p.read_text(encoding='utf-8'))
            p.write_text(first, encoding='utf-8')
            second = installer.patch_content(p, p.read_text(encoding='utf-8'))
            self.assertEqual(first, second)
            self.assertEqual(second.count('GW_BUSINESS_HOME_START'), 1)
            self.assertEqual(second.count('GW_SPONSOR_START'), 1)

    def test_traffic_blocks_are_exactly_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'trafico.html'
            p.write_text(
                '<html><head></head><body><main>'
                '<section class="gw-live-ledger"></section>'
                '<section class="gt-editorial-record"></section>'
                '</main><footer></footer></body></html>',
                encoding='utf-8',
            )
            first = installer.patch_content(p, p.read_text(encoding='utf-8'))
            p.write_text(first, encoding='utf-8')
            second = installer.patch_content(p, p.read_text(encoding='utf-8'))
            self.assertEqual(first, second)
            self.assertEqual(second.count('GW_QUICK_TRAFFIC_START'), 1)
            self.assertEqual(second.count('GW_SPONSOR_START'), 1)


if __name__ == '__main__':
    unittest.main()
