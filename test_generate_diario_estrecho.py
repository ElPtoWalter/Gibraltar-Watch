import os
import unittest
from unittest.mock import patch
import generate_diario_estrecho as g


class DiaryTests(unittest.TestCase):
    def item(self, title, category, weight=3, domain='example.com'):
        return {
            'title': title,
            'source': domain,
            'url': f'https://{domain}/{title.lower().replace(" ", "-")}',
            'published_at': g.NOW_UTC.isoformat(),
            'category': category,
            'weight': weight,
        }

    def test_select_prefers_diverse_categories(self):
        items = [
            self.item('Ceuta frontera novedades', 'ceuta', 5, 'a.es'),
            self.item('Algeciras trafico estable', 'traffic', 5, 'b.es'),
            self.item('Relacion bilateral agenda', 'relations', 4, 'c.es'),
        ]
        out = g.select_items(items)
        self.assertEqual(len(out), 3)
        self.assertEqual(len({i['category'] for i in out}), 3)

    def test_select_limits_same_domain(self):
        items = [self.item(f'Titular suficientemente distinto numero {n}', 'traffic', 4, 'same.es') for n in range(5)]
        out = g.select_items(items)
        self.assertLessEqual(len(out), g.MAX_PER_DOMAIN)

    def test_select_rejects_unsafe_url(self):
        bad = self.item('Titular valido pero URL mala', 'traffic', 5)
        bad['url'] = 'javascript:alert(1)'
        self.assertEqual(g.select_items([bad]), [])

    def test_full_mode_for_high_priority_day(self):
        items = [
            self.item('Incidente de trafico relevante uno', 'traffic', 5, 'a.es'),
            self.item('Puerto anuncia novedad operativa dos', 'ports', 5, 'b.es'),
            self.item('Ceuta registra novedad fronteriza tres', 'ceuta', 5, 'c.es'),
            self.item('Agenda bilateral incorpora novedad cuatro', 'relations', 4, 'd.es'),
            self.item('Logistica regional registra cambio cinco', 'economy', 4, 'e.es'),
        ]
        selected = g.select_items(items)
        self.assertEqual(g.edition_mode({}, selected), 'full')

    def test_brief_mode_for_quiet_day(self):
        items = [self.item('Novedad menor de jornada tranquila', 'economy', 1, 'a.es')]
        selected = g.select_items(items)
        self.assertEqual(g.edition_mode({}, selected), 'brief')

    def test_zero_source_brief_is_noindex(self):
        self.assertFalse(g.seo_indexable('brief', {}, []))

    def test_alert_can_make_zero_source_brief_indexable(self):
        status = {'maritime_status': {'es': 'INCIDENCIA'}}
        self.assertTrue(g.seo_indexable('brief', status, []))

    def test_article_escapes_source_title(self):
        item = self.item('<script>alert(1)</script> noticia', 'traffic', 3)
        draft = {
            'headline': 'Titular seguro para la edición diaria del Estrecho',
            'deck': 'Resumen suficientemente largo y seguro para explicar la edición del Estrecho de Gibraltar sin inventar hechos.',
            'situation': ['Situación.'],
            'sections': [{'title': 'Tráfico marítimo', 'paragraph': 'Contexto.'}],
            'meaning': ['Lectura.'],
            'watch': ['Vigilar avisos.'],
        }
        entries = [{'date': g.NOW.date().isoformat(), 'url': f'diario/{g.NOW.date().isoformat()}.html'}]
        html = g.article_html(g.NOW.date().isoformat(), g.NOW.isoformat(timespec='minutes'), g.NOW.isoformat(timespec='minutes'), {}, [item], 'abc', draft, 'brief', True, entries, 'rules')
        self.assertNotIn('<script>alert(1)</script> noticia', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('href="/diario.css?v=20260815-3"', html)
        self.assertIn(f'https://estrechogibraltar.com/diario/{g.NOW.date().isoformat()}.html', html)

    def test_build_draft_falls_back_without_api(self):
        with patch.object(g, 'AI_ENABLED', False):
            draft, engine = g.build_draft({}, [], 'brief')
        self.assertEqual(engine, 'rules')
        self.assertTrue(draft['headline'])


if __name__ == '__main__':
    unittest.main()
