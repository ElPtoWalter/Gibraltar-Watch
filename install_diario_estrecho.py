#!/usr/bin/env python3
"""Instala la capa visual/navegación del Diario del Estrecho de forma idempotente."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
HTMLS = list(ROOT.glob("*.html"))
CSS_TAG = '<link rel="stylesheet" href="/diario.css?v=20260815-3">'
LEGACY_JS_RE = re.compile(r'\s*<script defer src="diario\.js\?v=[^"]+"></script>\s*', re.I)
HOME_START = '<!-- GW_DIARIO_HOME_START -->'
HOME_END = '<!-- GW_DIARIO_HOME_END -->'
HOME_BLOCK = '''<!-- GW_DIARIO_HOME_START -->
<section class="gw-diary-home" aria-labelledby="gw-diary-title">
  <div>
    <p class="gw-business-kicker">EL DIARIO · HOY</p>
    <span class="gd-date">PRÓXIMA EDICIÓN</span>
    <h2 id="gw-diary-title">Diario del Estrecho</h2>
    <p>Una pieza diaria con contexto, fuentes y una lectura de qué importa realmente.</p>
    <a href="/diario/">Abrir hemeroteca →</a>
  </div>
  <div class="gw-diary-side">
    <p class="gw-business-kicker">EN PREPARACIÓN</p>
    <h3>La primera edición se publicará desde las 07:00</h3>
    <p>Los días tranquilos se publica un parte breve; cuando la jornada lo merece, un artículo completo.</p>
    <a href="/diario/">Ver el diario →</a>
  </div>
</section>
<!-- GW_DIARIO_HOME_END -->'''


def is_english(s: str) -> bool:
    return bool(re.search(r'<html[^>]+lang=["\']en(?:-[A-Za-z-]+)?["\']', s, re.I))


def ensure_head(s: str) -> str:
    s = LEGACY_JS_RE.sub("\n", s)
    # Sustituye versiones anteriores del CSS del diario por una sola versión actual.
    s = re.sub(r'<link rel="stylesheet" href="diario\.css\?v=[^"]+">', CSS_TAG, s, flags=re.I)
    if CSS_TAG not in s:
        s = s.replace('</head>', CSS_TAG + '\n</head>', 1)
    return s


def ensure_nav(s: str) -> str:
    if is_english(s):
        return s
    # Normaliza cualquier enlace antiguo del Diario a la ruta canónica /diario/.
    s = re.sub(r'href=["\'](?:/?diario(?:\.html)?/?)["\']', 'href="/diario/"', s, flags=re.I)
    if 'href="/diario/"' in s:
        return s
    link = '<a href="/diario/">Diario</a>'
    patterns = [
        r'(<a href="fuentes\.html">Fuentes</a>)',
        r'(<a class="lang-switch" href="en\.html">EN</a>)',
    ]
    for pat in patterns:
        if re.search(pat, s):
            return re.sub(pat, link + r'\n  \1', s, count=1)
    return s


def ensure_home(s: str) -> str:
    if HOME_START in s and HOME_END in s:
        # No pisa una edición ya generada; solo arregla un bloque incompleto/placeholder.
        block = re.search(re.escape(HOME_START) + r'.*?' + re.escape(HOME_END), s, re.S)
        if block and ('href="/diario/' in block.group(0) or 'href="diario/' in block.group(0)):
            return s
        return re.sub(re.escape(HOME_START) + r'.*?' + re.escape(HOME_END), HOME_BLOCK, s, count=1, flags=re.S)
    for marker in ('<!-- GW_BUSINESS_HOME_END -->', '<!-- GWC_HOME_END -->'):
        if marker in s:
            return s.replace(marker, HOME_BLOCK + '\n' + marker, 1)
    # Fallback conservador: antes del contacto o del cierre de main.
    marker = '<section class="gwc-contact-cta"'
    if marker in s:
        return s.replace(marker, HOME_BLOCK + '\n' + marker, 1)
    return s.replace('</main>', HOME_BLOCK + '\n</main>', 1)


def main() -> int:
    changed = []
    for p in HTMLS:
        if p.name.startswith('diario-') or p.name == 'diario.html':
            continue
        s = p.read_text(encoding='utf-8')
        if is_english(s):
            # No enlazamos una sección española como si fuera una edición inglesa.
            new = LEGACY_JS_RE.sub("\n", s)
        else:
            new = ensure_head(s)
            new = ensure_nav(new)
            if p.name == 'index.html':
                new = ensure_home(new)
        if new != s:
            p.write_text(new, encoding='utf-8')
            changed.append(p.name)
    print('Diario instalado/actualizado en', len(changed), 'páginas')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
