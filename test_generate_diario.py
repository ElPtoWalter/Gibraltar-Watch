import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import generate_diario as gd

class GenerateDiaryTests(unittest.TestCase):
    def make_root(self):
        td=tempfile.TemporaryDirectory(); root=Path(td.name)
        (root/'diario-config.json').write_text(json.dumps({
            'timezone':'Europe/Madrid','publish_after_local_hour':6,'lookback_hours':36,'extended_lookback_hours':72,
            'max_sources':7,'full_article_min_sources':3,'full_article_min_score':12,'ai_mode':'off','base_url':'https://estrechogibraltar.com'
        }),encoding='utf-8')
        (root/'index.html').write_text('<html><head></head><body><main><!-- GW_DIARY_HOME_START --><p>x</p><!-- GW_DIARY_HOME_END --></main></body></html>',encoding='utf-8')
        (root/'sitemap.xml').write_text('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://estrechogibraltar.com/</loc></url></urlset>',encoding='utf-8')
        geo={'status':{'maritime_status':{'es':'OPERATIVO'},'border_pressure':{'es':'ALTA'},'bilateral_tension':{'es':'VIGILANCIA'},'security_status':{'es':'VIGILANCIA'},'confidence':{'es':'ALTA'}},'items':[
            {'title':'Ceuta afronta nuevas medidas tras la crisis fronteriza','source':'Reuters','url':'https://example.com/1','published_at':'2026-08-10T05:00:00+00:00','category':'ceuta','language':'es','weight':5},
            {'title':'España y Marruecos mantienen contactos sobre la frontera','source':'EFE','url':'https://example.com/2','published_at':'2026-08-10T04:00:00+00:00','category':'relations','language':'es','weight':4},
            {'title':'El puerto de Algeciras mantiene su operativa','source':'APBA','url':'https://example.com/3','published_at':'2026-08-10T03:00:00+00:00','category':'ports','language':'es','weight':5},
            {'title':'Tráfico marítimo sin interrupciones en el corredor','source':'RTVE','url':'https://example.com/4','published_at':'2026-08-10T02:00:00+00:00','category':'traffic','language':'es','weight':4}
        ]}
        (root/'geopolitics.json').write_text(json.dumps(geo),encoding='utf-8')
        return td,root

    def test_generates_article_archive_rss_and_home(self):
        td,root=self.make_root()
        try:
            now=datetime(2026,8,10,6,30,tzinfo=timezone.utc)
            entry=gd.generate(root=root,now=now,force=True,allow_early=True,disable_ai=True)
            self.assertTrue((root/'diario'/'2026-08-10.html').exists())
            self.assertTrue((root/'diario'/'index.html').exists())
            self.assertTrue((root/'diario'/'feed.xml').exists())
            self.assertTrue(entry['indexable'])
            self.assertIn('Leer la edición de hoy', (root/'index.html').read_text(encoding='utf-8'))
            before=(root/'diario'/'2026-08-10.html').read_text(encoding='utf-8')
            gd.generate(root=root,now=now,force=False,allow_early=True,disable_ai=True)
            after=(root/'diario'/'2026-08-10.html').read_text(encoding='utf-8')
            self.assertEqual(before,after)
        finally: td.cleanup()

if __name__=='__main__': unittest.main()
