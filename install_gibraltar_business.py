from __future__ import annotations

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

VERSION = "20260804-1"
TODAY = "2026-08-04"
ROOT = Path(__file__).resolve().parent
FRAGMENTS = json.loads((ROOT / "gw-business-fragments.json").read_text(encoding="utf-8"))

ASSETS = (
    f'<meta name="gw:last-reviewed" content="{TODAY}">\n'
    f'<link rel="stylesheet" href="gw-business.css?v={VERSION}">\n'
    f'<script defer src="gw-monetization-config.js?v={VERSION}"></script>\n'
    f'<script defer src="gw-business.js?v={VERSION}"></script>\n'
)


def remove_block(text: str, start: str, end: str) -> str:
    pattern = (
        r'[ \t]*(?:\r?\n)?'
        + re.escape(start)
        + r'.*?'
        + re.escape(end)
        + r'[ \t]*(?:\r?\n)?'
    )
    return re.sub(pattern, '\n', text, flags=re.S)


def insert_before(text: str, needle: str, block: str) -> str:
    index = text.find(needle)
    if index < 0:
        return text
    before = text[:index].rstrip()
    after = text[index:].lstrip()
    return before + '\n\n' + block.strip() + '\n' + after


def insert_after_first(text: str, pattern: str, block: str) -> str:
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return text
    before = text[:match.end()].rstrip()
    after = text[match.end():].lstrip()
    return before + '\n' + block.strip() + '\n' + after


def patch_base(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'\s*<script[^>]+gibraltar-ui-fixes\.js[^>]*></script>', '', text)
    text = re.sub(r'\s*<link[^>]+gw-business\.css[^>]*>', '', text)
    text = re.sub(r'\s*<script[^>]+gw-monetization-config\.js[^>]*></script>', '', text)
    text = re.sub(r'\s*<script[^>]+gw-business\.js[^>]*></script>', '', text)
    text = re.sub(r'\s*<meta[^>]+name="gw:last-reviewed"[^>]*>', '', text)
    if '</head>' in text:
        index = text.find('</head>')
        before = text[:index].rstrip()
        after = text[index:].lstrip()
        text = before + '\n' + ASSETS + after
    if 'gw-business-footer-links' not in text and '</footer>' in text:
        english = path.name.startswith('en-') or path.name == 'en.html'
        links = (
            '<div class="gw-business-footer-links"><a href="en-advertise.html">Advertising</a><a href="en-cookies.html">Cookies</a></div>'
            if english else
            '<div class="gw-business-footer-links"><a href="publicidad-y-patrocinios.html">Publicidad y patrocinios</a><a href="cookies.html">Cookies</a></div>'
        )
        text = text.replace('</footer>', links + '</footer>', 1)
    return text


def patch_content(path: Path, text: str) -> str:
    name = path.name
    if name in {'index.html', 'en.html'}:
        text = remove_block(text, '<!-- GW_BUSINESS_HOME_START -->', '<!-- GW_BUSINESS_HOME_END -->')
        text = insert_before(text, '<section class="gwc-traffic-economy"', FRAGMENTS['home_en' if name == 'en.html' else 'home_es'])
        text = remove_block(text, '<!-- GW_SPONSOR_START -->', '<!-- GW_SPONSOR_END -->')
        text = insert_before(text, '<section class="gwc-contact-cta"', FRAGMENTS['sponsor_en' if name == 'en.html' else 'sponsor_es'])

    elif name in {'trafico.html', 'en-traffic.html'}:
        text = remove_block(text, '<!-- GW_QUICK_TRAFFIC_START -->', '<!-- GW_QUICK_TRAFFIC_END -->')
        text = insert_after_first(text, r'<section class="gw-live-ledger".*?</section>', FRAGMENTS['quick_traffic_en' if name.startswith('en-') else 'quick_traffic_es'])
        text = remove_block(text, '<!-- GW_SPONSOR_START -->', '<!-- GW_SPONSOR_END -->')
        sponsor = FRAGMENTS['sponsor_en' if name.startswith('en-') else 'sponsor_es']
        text = insert_before(text, '<section class="gt-editorial-record', sponsor) if '<section class="gt-editorial-record' in text else insert_before(text, '</main>', sponsor)

    elif name in {'importancia.html', 'en-importance.html'}:
        text = text.replace('<h1>Por qué Gibraltar es un punto estratégico</h1>', '<h1>Por qué el Estrecho de Gibraltar es estratégico</h1>')
        text = text.replace('<h1>Why Gibraltar is a strategic point</h1>', '<h1>Why the Strait of Gibraltar is strategically important</h1>')
        text = remove_block(text, '<!-- GW_QUICK_IMPORTANCE_START -->', '<!-- GW_QUICK_IMPORTANCE_END -->')
        text = insert_after_first(text, r'<section class="inner-hero[^>]*>.*?</section>', FRAGMENTS['quick_importance_en' if name.startswith('en-') else 'quick_importance_es'])
        text = remove_block(text, '<!-- GW_SPONSOR_START -->', '<!-- GW_SPONSOR_END -->')
        text = insert_before(text, '</main>', FRAGMENTS['sponsor_en' if name.startswith('en-') else 'sponsor_es'])

    elif name in {
        'servicios-buques-estrecho-gibraltar.html', 'en-ship-services-strait-gibraltar.html',
        'operacion-paso-estrecho-2026.html', 'en-strait-crossing-operation-2026.html'
    }:
        text = remove_block(text, '<!-- GW_SPONSOR_START -->', '<!-- GW_SPONSOR_END -->')
        sponsor = FRAGMENTS['sponsor_en' if name.startswith('en-') else 'sponsor_es']
        text = insert_before(text, '<section class="gt-editorial-record', sponsor) if '<section class="gt-editorial-record' in text else insert_before(text, '</main>', sponsor)

    elif name in {'privacidad.html', 'en-privacy.html'}:
        text = remove_block(text, '<!-- GW_PRIVACY_ADS_START -->', '<!-- GW_PRIVACY_ADS_END -->')
        text = insert_before(text, '</main>', FRAGMENTS['privacy_en' if name.startswith('en-') else 'privacy_es'])

    return text


def patch_html(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    text = patch_content(path, patch_base(path))
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def rebuild_sitemap() -> None:
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    root = ET.Element(f'{{{ns}}}urlset')
    priority = {
        'index.html':'1.0','trafico.html':'0.9','situacion-actual.html':'0.9','importancia.html':'0.9',
        'en.html':'0.9','publicidad-y-patrocinios.html':'0.6','en-advertise.html':'0.6','cookies.html':'0.4','en-cookies.html':'0.4'
    }
    for path in sorted((p for p in ROOT.glob('*.html') if p.name != '404.html'), key=lambda p: (p.name != 'index.html', p.name)):
        url = ET.SubElement(root, f'{{{ns}}}url')
        loc = ET.SubElement(url, f'{{{ns}}}loc')
        loc.text = 'https://estrechogibraltar.com/' if path.name == 'index.html' else f'https://estrechogibraltar.com/{path.name}'
        ET.SubElement(url, f'{{{ns}}}lastmod').text = TODAY
        freq = 'daily' if 'situacion' in path.name or 'current-situation' in path.name else ('hourly' if 'sismicidad' in path.name or 'seismicity' in path.name else 'weekly')
        ET.SubElement(url, f'{{{ns}}}changefreq').text = freq
        ET.SubElement(url, f'{{{ns}}}priority').text = priority.get(path.name, '0.7')
    ET.ElementTree(root).write(ROOT / 'sitemap.xml', encoding='utf-8', xml_declaration=True)


def main() -> None:
    changed = sum(patch_html(path) for path in ROOT.glob('*.html'))
    rebuild_sitemap()
    print(f'Gibraltar business layer applied to {changed} files.')


if __name__ == '__main__':
    main()
