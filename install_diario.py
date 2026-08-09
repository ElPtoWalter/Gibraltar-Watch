#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
CSS_TAG = '<link rel="stylesheet" href="diario.css?v=20260810-1">'
START = '<!-- GW_DIARY_HOME_START -->'
END = '<!-- GW_DIARY_HOME_END -->'

HOME_PLACEHOLDER = f'''{START}
<section class="gw-diary-home" aria-labelledby="gw-diary-home-title">
  <div class="gw-diary-home__mast"><small>EDICIÓN DIARIA</small><strong>DIARIO<br>DEL<br>ESTRECHO</strong><span>Una lectura cada mañana</span></div>
  <div class="gw-diary-home__story"><div class="gw-diary-home__meta"><span>Actualización diaria</span><span>Fuentes enlazadas</span></div><h2 id="gw-diary-home-title">La jornada del Estrecho, explicada con contexto</h2><p>Tráfico marítimo, puertos, Ceuta y Melilla, España–Marruecos y los sucesos que realmente cambian la lectura del corredor.</p><a class="gw-diary-home__link" href="diario/">Abrir Diario del Estrecho →</a></div>
</section>
{END}'''


def patch_home(text: str) -> str:
    if CSS_TAG not in text:
        text = text.replace('</head>', CSS_TAG + '\n</head>', 1)
    if START in text and END in text:
        # Conserva la tarjeta de la última edición; generate_diario.py la actualiza cuando toque.
        return text
    else:
        anchor = '<!-- GW_BUSINESS_HOME_START -->'
        if anchor in text:
            text = text.replace(anchor, HOME_PLACEHOLDER + '\n' + anchor, 1)
        elif '<section class="gwc-traffic-economy"' in text:
            text = text.replace('<section class="gwc-traffic-economy"', HOME_PLACEHOLDER + '\n<section class="gwc-traffic-economy"', 1)
        else:
            text = text.replace('</main>', HOME_PLACEHOLDER + '\n</main>', 1)
    return text


def add_diary_nav(text: str) -> str:
    if 'href="diario/">Diario</a>' not in text:
        text = re.sub(r'(<a href="situacion-actual\.html"[^>]*>Situación actual</a>)', r'\1\n  <a href="diario/">Diario</a>', text, count=1)
    return text


def add_footer_link(text: str) -> str:
    if 'href="diario/">Diario del Estrecho</a>' not in text:
        text = re.sub(r'(<section><h2>Observatorio</h2>)', r'\1<a href="diario/">Diario del Estrecho</a>', text, count=1)
    return text


def is_spanish_page(path: Path) -> bool:
    return path.suffix == '.html' and not path.name.startswith('en-') and path.name != 'en.html'


def main() -> int:
    changed = 0
    index = ROOT / 'index.html'
    if index.exists():
        old = index.read_text(encoding='utf-8')
        new = add_footer_link(add_diary_nav(patch_home(old)))
        if new != old:
            index.write_text(new, encoding='utf-8')
            changed += 1
    for path in ROOT.glob('*.html'):
        if path.name == 'index.html' or not is_spanish_page(path):
            continue
        old = path.read_text(encoding='utf-8')
        new = add_footer_link(add_diary_nav(old))
        if new != old:
            path.write_text(new, encoding='utf-8')
            changed += 1
    print(f'Diario del Estrecho instalado/validado en {changed} archivo(s).')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
