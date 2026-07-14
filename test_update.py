import unittest, json
from pathlib import Path
class TestConfig(unittest.TestCase):
 def test_region(self):
  c=json.loads(Path('config.json').read_text())
  r=c['region']; self.assertLess(r['min_lat'],36); self.assertGreater(r['max_lat'],36); self.assertLess(r['min_lon'],-5.5); self.assertGreater(r['max_lon'],-5.5)
 def test_counterfactual(self):
  c=json.loads(Path('config.json').read_text()); years=c['narrowest_width_km']*1_000_000/c['plate_convergence_mm_year']; self.assertGreater(years,2_000_000); self.assertLess(years,5_000_000)
 def test_json(self):
  for f in ['seismicity.json','seismic-history.json','sources.json','project-status.json']: json.loads(Path(f).read_text())
if __name__=='__main__':unittest.main()
