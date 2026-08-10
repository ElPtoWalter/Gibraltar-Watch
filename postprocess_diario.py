#!/usr/bin/env python3
"""Add the Gibraltar Watch editorial trust layer to Diario del Estrecho pages.

The Diario content remains untouched; this postprocessor only adds editorial
standards/navigation UI and never rewrites reported facts.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DIARY=ROOT/'diario'
CSS='<link rel="stylesheet" href="../gw-observatory.css?v=20260810-1">'
JS='<script defer src="../gw-observatory.js?v=20260810-1"></script>'
START='<!-- GWO_DIARY_TRUST_START -->'; END='<!-- GWO_DIARY_TRUST_END -->'
TRUST=f'''{START}<div class="gwo-trust-strip" aria-label="Criterio editorial"><span><b>HECHOS</b> · atribuidos y enlazados</span><span><b>INTERPRETACIÓN</b> · separada</span><span><b>ESCENARIOS</b> · no se publican como hechos</span><span><a href="../transparencia.html">Estándares editoriales →</a></span></div>{END}'''


def patch(text:str)->str:
    if 'gw-observatory.css' not in text and '</head>' in text:
        text=text.replace('</head>',CSS+'\n'+JS+'\n</head>',1)
    if START in text and END in text:
        text=re.sub(re.escape(START)+r'.*?'+re.escape(END),lambda _:TRUST,text,count=1,flags=re.S)
    elif 'class="diary-byline"' in text:
        m=re.search(r'<div class="diary-byline"[^>]*>.*?</div>',text,re.S)
        if m:
            text=text[:m.end()]+TRUST+text[m.end():]
    if 'href="../transparencia.html"' not in text and '</footer>' in text:
        text=text.replace('</footer>','<a href="../transparencia.html">Transparencia</a><a href="../correcciones.html">Correcciones</a></footer>',1)
    return text


def main()->int:
    if not DIARY.exists():
        print('Diario aún no existe; no hay nada que postprocesar.')
        return 0
    changed=0
    for path in DIARY.glob('*.html'):
        old=path.read_text(encoding='utf-8'); new=patch(old)
        if new!=old:
            path.write_text(new,encoding='utf-8'); changed+=1
    print(f'Diario: capa de transparencia vNext aplicada en {changed} archivo(s).')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
