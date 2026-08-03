import unittest
from update_ope import parse_date,rows,totals
class OpeParserTests(unittest.TestCase):
 def test_date(self):self.assertEqual(parse_date('1 de agosto de 2026').isoformat(),'2026-08-01')
 def test_rows(self):
  r=rows('Algeciras/Tánger-Med 35 25482 7312')
  self.assertEqual(r[0]['passengers'],25482)
 def test_totals(self):
  d=totals('Total general día 86 49908 13404',r'Total general d[ií]a')
  self.assertEqual(d['vehicles'],13404)
if __name__=='__main__':unittest.main()
