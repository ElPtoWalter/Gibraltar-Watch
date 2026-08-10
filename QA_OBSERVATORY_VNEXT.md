# QA · Observatory vNext

## Pruebas automatizadas del paquete

- Python: compilación correcta de todos los scripts vNext.
- JavaScript: `node --check` superado para `gw-observatory.js`.
- YAML: ambos workflows cargan correctamente con parser YAML.
- CSS: llaves equilibradas.
- Unit tests: **11/11 superados**.

Las pruebas cubren, entre otros puntos:

- un cierre marítimo eleva el estado a alerta operativa;
- tensión política/fronteriza no se convierte en cierre;
- “SIN ALERTA ESPECÍFICA” no produce un falso positivo;
- anomalías no aparecen antes de disponer de histórico suficiente;
- esquema actual de `seismicity.json` y `ope-2026.json` compatible;
- instalador de portada idempotente;
- fallback cuando no existe la clase hero esperada;
- postprocesado del Diario idempotente y sin reescribir el texto factual;
- output de alertas de alta prioridad.

## Simulación integral

Se ejecutó en un repositorio de prueba la cadena completa:

`install_gibraltar_observatory.py` → `postprocess_diario.py` → `update_observatory.py` → `generate_newsletter.py` → `emit_observatory_alert.py` → `build_publication_manifest.py` → `validate_gibraltar.py`.

Resultado: **VALIDACIÓN OK · 0 avisos · publicación segura para commit**.

## Protección del workflow

El validador bloquea el commit si:

- falta un archivo crítico;
- aparece JSON/XML/JSON-LD inválido;
- faltan las páginas vNext en el sitemap;
- se rompe una referencia local en las páginas nuevas;
- desaparecen los bloques vNext de las páginas principales;
- falta la trazabilidad del Diario;
- cambia un archivo después de generar el manifiesto de checksums;
- vuelve a aparecer `submit_gibraltar_inde`;
- se vuelve a ocultar IndexNow mediante `continue-on-error: true`;
- falta una etapa vNext del workflow.
