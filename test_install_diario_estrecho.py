import unittest
import install_diario_estrecho as i


class InstallerTests(unittest.TestCase):
    def test_head_is_idempotent_and_removes_legacy_js(self):
        s = '<html lang="es"><head></head><body><script defer src="diario.js?v=20260815-1"></script></body></html>'
        once = i.ensure_head(s)
        twice = i.ensure_head(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count('diario.css'), 1)
        self.assertNotIn('diario.js', once)

    def test_spanish_nav_is_idempotent(self):
        s = '<html lang="es"><nav><a href="fuentes.html">Fuentes</a></nav></html>'
        once = i.ensure_nav(s)
        twice = i.ensure_nav(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count('href="/diario/"'), 1)

    def test_english_nav_is_not_modified(self):
        s = '<html lang="en"><nav><a href="en-sources.html">Sources</a></nav></html>'
        self.assertEqual(i.ensure_nav(s), s)

    def test_home_is_idempotent(self):
        s = '<html lang="es"><body><main><!-- GWC_HOME_END --></main></body></html>'
        once = i.ensure_home(s)
        twice = i.ensure_home(once)
        self.assertEqual(once, twice)
        self.assertEqual(once.count(i.HOME_START), 1)


if __name__ == '__main__':
    unittest.main()
