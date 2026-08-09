import tempfile
import unittest
from pathlib import Path
import install_diario as mod

class InstallDiaryTests(unittest.TestCase):
    def test_home_patch_is_idempotent(self):
        html='''<html><head></head><body><nav><a href="situacion-actual.html">Situación actual</a></nav><main><!-- GW_BUSINESS_HOME_START --></main><footer><section><h2>Observatorio</h2></section></footer></body></html>'''
        once=mod.add_footer_link(mod.add_diary_nav(mod.patch_home(html)))
        twice=mod.add_footer_link(mod.add_diary_nav(mod.patch_home(once)))
        self.assertEqual(once, twice)
        self.assertEqual(once.count(mod.START),1)
        self.assertEqual(once.count('href="diario/">Diario</a>'),1)
        self.assertEqual(once.count('diario.css'),1)

if __name__=='__main__': unittest.main()
